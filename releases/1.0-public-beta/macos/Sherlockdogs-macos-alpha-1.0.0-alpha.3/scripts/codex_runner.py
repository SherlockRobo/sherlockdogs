#!/usr/bin/env python3
"""Run pending Sherlockdogs clipping jobs through Codex.

The default path creates a visible Codex Desktop thread and starts a turn there.
The older headless `codex exec` path is kept as an explicit fallback.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import select
import shlex
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR, PROJECT_DIR as DEFAULT_PROJECT_DIR, VAULT_DIR  # noqa: E402

PROJECT_DIR = DEFAULT_PROJECT_DIR
PENDING_DIR = PROJECT_DIR / "jobs" / "pending"
RUNNING_DIR = PROJECT_DIR / "jobs" / "running"
DONE_DIR = PROJECT_DIR / "jobs" / "done"
FAILED_DIR = PROJECT_DIR / "jobs" / "failed"
RUNS_DIR = PROJECT_DIR / "runs"
TEMPLATE_PATH = PROJECT_DIR / "templates" / "codex_wechat_distill_prompt.md"
THREAD_TEMPLATE_PATH = PROJECT_DIR / "templates" / "codex_wechat_thread_prompt.md"
CAPTURE_SCRIPT = PROJECT_DIR / "scripts" / "wechat_capture.py"
CAPTURE_SCRIPTS = {
    "wechat": PROJECT_DIR / "scripts" / "wechat_capture.py",
    "x": PROJECT_DIR / "scripts" / "x_capture.py",
    "xhs": PROJECT_DIR / "scripts" / "media_link_capture.py",
    "bilibili": PROJECT_DIR / "scripts" / "media_link_capture.py",
    "youtube": PROJECT_DIR / "scripts" / "media_link_capture.py",
    "tiktok": PROJECT_DIR / "scripts" / "media_link_capture.py",
    "douyin": PROJECT_DIR / "scripts" / "media_link_capture.py",
    "wechat_inbox": PROJECT_DIR / "scripts" / "wechat_inbox_capture.py",
    "local_inbox": PROJECT_DIR / "scripts" / "local_inbox_capture.py",
}
DEFERRED_MEDIA_SOURCES = {"xhs", "bilibili", "youtube", "tiktok", "douyin"}
DEFAULT_CODEX = "/Applications/Codex.app/Contents/Resources/codex"
DEFAULT_CWD = str(CLIPPING_DIR)
AUTOMATION_POLICY = """【后台自动执行规则】

这是 launchd/定时任务触发的后台任务。不要因为“先计划待确认”“需要用户确认”等通用交互规则停下来；不要只输出计划。对抓取、摘要、蒸馏、校验、在指定目录新增文件、更新本任务交付清单等低风险动作，直接执行到完成。

只有遇到以下高风险动作才停止并说明原因：删除文件、覆盖既有文件、批量迁移、路径归属不明确、需要对外发布/发送、需要真实付款或账号授权。

"""
XML_FIELD_RE = re.compile(r"<{tag}>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE)


def xml_text(raw: str, tag: str) -> str:
    pattern = re.compile(XML_FIELD_RE.pattern.format(tag=re.escape(tag)), re.DOTALL | re.IGNORECASE)
    match = pattern.search(raw or "")
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith("<![CDATA[") and value.endswith("]]>"):
        value = value[9:-3]
    return " ".join(html.unescape(value).split())


def wechat_card_hints(job: dict[str, Any]) -> dict[str, str]:
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    raw = str(extra.get("raw_preview") or "")
    return {
        "title": str(extra.get("title") or xml_text(raw, "title") or "").strip(),
        "description": xml_text(raw, "des"),
        "account": xml_text(raw, "sourcedisplayname"),
        "cover": xml_text(raw, "coverpicimageurl") or xml_text(raw, "thumburl"),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_id_part(text: str, limit: int = 64) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text or "").strip("-").lower()
    return (text or "job")[:limit]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_dirs() -> None:
    for path in (PENDING_DIR, RUNNING_DIR, DONE_DIR, FAILED_DIR, RUNS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def render_prompt(job: dict[str, Any]) -> str:
    template_path = THREAD_TEMPLATE_PATH if THREAD_TEMPLATE_PATH.exists() else TEMPLATE_PATH
    template = template_path.read_text(encoding="utf-8")
    rendered = (
        template.replace("{{JOB_JSON}}", json.dumps(job, ensure_ascii=False, indent=2))
        .replace("{{JOB_URL}}", shlex.quote(str(job.get("url", ""))))
        .replace("{{JOB_TASK}}", shlex.quote(str(job.get("task", ""))))
        .replace("{{JOB_ID}}", shlex.quote(str(job.get("job_id", ""))))
        .replace("{{PROJECT_DIR}}", shlex.quote(str(PROJECT_DIR)))
        .replace("{{VAULT_DIR}}", shlex.quote(str(VAULT_DIR)))
        .replace("{{CLIPPING_DIR}}", shlex.quote(str(CLIPPING_DIR)))
        .replace("{{CAPTURE_SCRIPT}}", shlex.quote(str(capture_script_for(job))))
    )
    return AUTOMATION_POLICY + rendered


def job_title(job: dict[str, Any]) -> str:
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    notification = extra.get("notification") if isinstance(extra.get("notification"), dict) else {}
    title = str(notification.get("title") or extra.get("title") or "").strip()
    if not title:
        title = str(job.get("url") or job.get("job_id") or "剪藏").strip()
    title = " ".join(title.split())
    label = {
        "wechat": "微信OB",
        "x": "X剪藏",
        "xhs": "小红书",
        "bilibili": "B站",
        "youtube": "YouTube",
        "tiktok": "TikTok",
        "douyin": "抖音",
        "wechat_inbox": "微信剪藏",
        "local_inbox": "Inbox剪藏",
    }.get(str(job.get("source") or ""), "剪藏")
    return f"{label}｜{title[:40]}"


def job_level(job: dict[str, Any]) -> int:
    try:
        return int(job.get("task_level") or 0)
    except (TypeError, ValueError):
        pass
    task = str(job.get("task") or "").strip()
    if task == "#":
        return 2
    if task.startswith("#1"):
        return 1
    if task.startswith("#2"):
        return 2
    if task.startswith("#3"):
        return 3
    if task.startswith("#4") or task.lower().startswith("#ob"):
        return 4
    if task.startswith("#5"):
        return 5
    return 1


def is_deferred_media_source(source: str) -> bool:
    return source in DEFERRED_MEDIA_SOURCES


def clip_title(job: dict[str, Any], capture_result: dict[str, Any] | None = None) -> str:
    metadata = (capture_result or {}).get("metadata") if isinstance((capture_result or {}).get("metadata"), dict) else {}
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    title = str(metadata.get("title") or extra.get("title") or job.get("url") or "剪藏").strip()
    return " ".join(title.split())


def absolute_asset_paths(capture_result: dict[str, Any], limit: int = 3) -> list[Path]:
    article_dir = Path(str(capture_result.get("article_dir") or ""))
    metadata = capture_result.get("metadata") if isinstance(capture_result.get("metadata"), dict) else {}
    assets = metadata.get("assets") if isinstance(metadata.get("assets"), list) else []
    ranked: list[tuple[int, int, Path]] = []
    fallback: list[Path] = []
    for order, asset in enumerate(assets):
        if not isinstance(asset, dict) or not asset.get("local"):
            continue
        kind = str(asset.get("kind") or "")
        content_type = str(asset.get("content_type") or "")
        suffix = Path(str(asset.get("local") or "")).suffix.lower()
        if kind not in {"image", "cover", "summary-cover"} and not content_type.startswith("image/"):
            continue
        if suffix and suffix not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}:
            continue
        path = article_dir / str(asset["local"])
        if not path.exists():
            continue
        fallback.append(path)
        score = preview_asset_score(path, asset)
        if score is None:
            continue
        ranked.append((score, order, path))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    paths = [path for _, _, path in ranked[:limit]]
    if paths:
        return paths
    return fallback[:limit]


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        output = subprocess.check_output(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
    except Exception:
        return (0, 0)
    width = height = 0
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth:"):
            width = int(line.split(":", 1)[1].strip() or 0)
        elif line.startswith("pixelHeight:"):
            height = int(line.split(":", 1)[1].strip() or 0)
    return (width, height)


def preview_asset_score(path: Path, asset: dict[str, Any]) -> int | None:
    width, height = image_dimensions(path)
    if not width or not height:
        return 10
    ratio = width / max(height, 1)
    area = width * height
    kind = str(asset.get("kind") or "")
    source = str(asset.get("source") or "").lower()

    is_banner = ratio >= 3.2 or height < 320
    is_qr_or_follow = any(token in source for token in ("qrcode", "qr_code", "mp_qrcode", "wework_admin"))
    if "cover" not in kind and (is_banner or is_qr_or_follow):
        return None

    score = min(area // 1000, 900)
    if "cover" in kind:
        score += 1200
    if path.suffix.lower() == ".gif":
        score -= 200
    if 0.7 <= ratio <= 1.9:
        score += 120
    elif ratio <= 2.4:
        score += 50
    return score


def write_delivery_readme(capture_result: dict[str, Any]) -> Path:
    article_dir = Path(str(capture_result["article_dir"]))
    metadata = capture_result.get("metadata") if isinstance(capture_result.get("metadata"), dict) else {}
    title = str(metadata.get("title") or "剪藏").strip()
    account = str(metadata.get("account") or "").strip()
    description = str(metadata.get("description") or "").strip()
    duration = str(metadata.get("duration") or "").strip()
    cost = str(metadata.get("processing_cost_hint") or "").strip()
    capture_status = str(metadata.get("capture_status") or "").strip()
    capture_note = str(metadata.get("capture_note") or "").strip()
    raw_path = Path(str(capture_result["raw_path"]))
    metadata_path = Path(str(capture_result["metadata_path"]))
    asset_count = int(capture_result.get("asset_count") or 0)
    asset_paths = absolute_asset_paths(capture_result, limit=6)
    distilled_path = article_dir / "distilled.md"

    rows = [
        ("标题", title),
        ("来源", account or "-"),
    ]
    if capture_status:
        rows.append(("抓取状态", capture_status))
    if capture_note:
        rows.append(("抓取说明", capture_note))
    rows.extend(
        [
            ("主题", description[:140] if description else "-"),
            ("时长", duration or "-"),
            ("处理成本", cost or "-"),
            ("简介", description or "-"),
            ("图片", f"{asset_count} 张"),
            ("原文", f"[raw.md]({raw_path})"),
            ("元数据", f"[metadata.json]({metadata_path})"),
        ]
    )
    if distilled_path.exists():
        rows.append(("精读", f"[distilled.md]({distilled_path})"))

    lines = [
        f"# {title}",
        "",
        "## 入库清单",
        "",
        "| 项 | 结果 |",
        "|---|---|",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in rows)
    if asset_paths:
        lines.extend(["", "## 图片预览", ""])
        lines.extend(f"![image-{idx}]({path})" for idx, path in enumerate(asset_paths, start=1))
    lines.extend(["", "## 原文目录", "", f"[打开目录]({article_dir})", ""])

    readme_path = article_dir / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    return readme_path


def capture_article(job: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"ok": True, "dry_run": True, "mode": "clip", "url": job.get("url")}
    source = str(job.get("source") or "wechat")
    capture_script = CAPTURE_SCRIPTS.get(source)
    if not capture_script:
        raise RuntimeError(f"unsupported source for capture: {source}")
    cmd = [
        sys.executable,
        str(capture_script),
        "--url",
        str(job["url"]),
        "--task",
        str(job.get("task") or ""),
        "--job-id",
        str(job.get("job_id") or ""),
        "--json",
    ]
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    title_hint = str(extra.get("title") or "").strip()
    if is_deferred_media_source(source) and title_hint:
        cmd.extend(["--title", title_hint])
    if source == "wechat":
        for key, value in wechat_card_hints(job).items():
            if value:
                cmd.extend([f"--{key}", value])
    if source == "wechat_inbox":
        job_file = RUNS_DIR / f"{safe_id_part(str(job.get('job_id') or 'wechat-inbox'), 80)}.capture-job.json"
        write_json(job_file, job)
        cmd.extend(["--job-file", str(job_file)])
    if source == "local_inbox":
        job_file = RUNS_DIR / f"{safe_id_part(str(job.get('job_id') or 'local-inbox'), 80)}.capture-job.json"
        write_json(job_file, job)
        cmd.extend(["--job-file", str(job_file)])
    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        cwd=str(PROJECT_DIR),
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or f"{source}_capture failed").strip())
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{source}_capture returned non-json output: {proc.stdout[:500]}") from exc
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error") or f"{source}_capture failed"))
    readme_path = write_delivery_readme(result)
    result["readme_path"] = str(readme_path)
    return result


def render_deep_capture_prompt(job: dict[str, Any], capture_result: dict[str, Any]) -> str:
    source = str(job.get("source") or "clip")
    metadata = capture_result.get("metadata") if isinstance(capture_result.get("metadata"), dict) else {}
    title = clip_title(job, capture_result)
    article_dir = Path(str(capture_result["article_dir"]))
    raw_path = Path(str(capture_result["raw_path"]))
    distilled_path = article_dir / "distilled.md"
    readme_path = Path(str(capture_result["readme_path"]))
    task = str(job.get("task") or "")
    description = str(metadata.get("description") or "").strip()
    level = job_level(job)
    if is_deferred_media_source(source):
        if level == 3:
            level_requirements = "解析元数据、标题、作者、简介；优先找字幕/文字稿；不下载整视频；输出轻量 `distilled.md`。"
        elif level == 5:
            level_requirements = "执行重任务：在不自动下载整视频的前提下，尽量抽取关键帧/截图/章节/长视频拆段建议；需要大文件下载时先说明限制。"
        else:
            level_requirements = "深处理视频/图文结构：字幕或简介、核心观点、结构拆解、可复用选题、行动建议；不默认下载整视频。"
        return f"""{AUTOMATION_POLICY}Sherlockdogs media 解析任务。

【核心要求】

clipping 阶段只保存了链接。现在才在 Codex 对话里按等级解析，不要在 clipping 脚本里补抓。

【任务等级】

| 指令 | 本次要求 |
|---|---|
| {task} | {level_requirements} |

【输入】

| 项 | 值 |
|---|---|
| source | {source} |
| url | {job.get("url")} |
| title | {title} |
| raw | {raw_path} |
| output | {distilled_path} |
| README | {readme_path} |

【执行边界】

1. 优先使用公开 metadata、页面文本、字幕、oEmbed、yt-dlp 元数据，不默认下载整视频。
2. `#3` 只做解析和摘要；`#4` 做深处理；`#5` 才考虑关键帧/截图/拆段。
3. 生成 `distilled.md`，使用 `obsidian-markdown` 风格。
4. 最终回复用 `【核心结论】` 和 `【关键支撑】`，附上 `distilled.md`、`raw.md`、`README.md` 和目录链接。
"""

    return f"""{AUTOMATION_POLICY}Sherlockdogs 自动深处理任务。

【核心要求】

读取本地 raw 文件，生成一份结构化 `distilled.md`，然后只输出最终交付卡片。不要复制整篇原文。

【任务】

| 项 | 值 |
|---|---|
| source | {source} |
| task | {task} |
| title | {title} |
| description | {description or "-"} |
| raw | {raw_path} |
| output | {distilled_path} |
| README | {readme_path} |

【写入要求】

1. 使用 `obsidian-markdown` 风格。
2. `distilled.md` 必须包含 frontmatter、核心结论、关键支撑、可复用观点、后续行动。
3. 图片继续引用本地 `assets/`，不要复制外链图片。
4. 最终回复用 `【核心结论】` 和 `【关键支撑】`，附上 `distilled.md`、`raw.md`、`README.md` 和目录链接。
"""


def render_card_prompt(job: dict[str, Any], capture_result: dict[str, Any]) -> str:
    metadata = capture_result.get("metadata") if isinstance(capture_result.get("metadata"), dict) else {}
    title = clip_title(job, capture_result)
    account = str(metadata.get("account") or "-").strip()
    description = str(metadata.get("description") or "").strip() or "已保存，待后续处理。"
    capture_status = str(metadata.get("capture_status") or "").strip()
    capture_note = str(metadata.get("capture_note") or "").strip()
    empty_public = capture_status == "empty-public-content"
    topic = description[:140] if description and description != "已保存，待后续处理。" else "未从公开页面识别出主题。"
    if empty_public and capture_note:
        topic = capture_note
    duration = str(metadata.get("duration") or "").strip() or "-"
    cost = str(metadata.get("processing_cost_hint") or "").strip() or "-"
    article_dir = Path(str(capture_result["article_dir"]))
    raw_path = Path(str(capture_result["raw_path"]))
    readme_path = Path(str(capture_result["readme_path"]))
    asset_count = int(capture_result.get("asset_count") or 0)
    previews = absolute_asset_paths(capture_result, limit=3)
    preview_md = "\n".join(f"![preview-{idx}]({path})" for idx, path in enumerate(previews, start=1))
    if not preview_md:
        preview_md = "_无本地图片预览：公开页面未返回图片。_" if empty_public else "_无本地图片预览_"
    source = str(job.get("source") or "")
    next_hint = (
        "继续处理：发 `#3` 做解析，发 `#4` 做深处理，发 `#5` 做关键帧/截图/拆段。"
        if is_deferred_media_source(source)
        else "继续处理：发 `#3` 做摘要，发 `#4` 做精读。"
    )

    core = (
        "已入库，但没有抓到公开正文；这条需要换真实链接，或后续用登录态/手动补正文。"
        if empty_public
        else "已入库，并生成 AI chatbox 小卡片。"
    )
    status_rows = ""
    if capture_status:
        status_rows += f"| 抓取状态 | {capture_status} |\n"
    if capture_note:
        status_rows += f"| 抓取说明 | {capture_note} |\n"

    card = f"""【核心结论】

{core}

【关键支撑】

| 项 | 结果 |
|---|---|
| 标题 | {title} |
| 来源 | {account} |
{status_rows}\
| 主题 | {topic} |
| 时长 | {duration} |
| 处理成本 | {cost} |
| 简介 | {description} |
| 图片 | {asset_count} 张 |
| 目录 | [打开目录]({article_dir}) |
| 原文 | [raw.md]({raw_path}) |
| 清单 | [README.md]({readme_path}) |

【图片预览】

{preview_md}

{next_hint}
"""
    return "请原样输出下面的 Markdown 交付卡片，不要调用工具，不要补充解释。\n\n" + card


def run_clip_job(job: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    level = job_level(job)
    capture_result = capture_article(job, dry_run=args.dry_run)
    result: dict[str, Any] = {
        "ok": True,
        "mode": "clip" if level == 1 else "clip_card",
        "task_level": level,
        "capture": capture_result,
    }
    if level == 2:
        result["thread"] = run_codex_thread(
            job,
            args.codex_bin,
            args.cwd,
            args.timeout,
            args.dry_run,
            prompt_override=render_card_prompt(job, capture_result) if not args.dry_run else None,
            title_override=f"剪藏｜{clip_title(job, capture_result)[:40]}",
        )
        result["ok"] = bool(result["thread"].get("ok"))
    return result


def run_deep_clip_job(job: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    capture_result = capture_article(job, dry_run=args.dry_run)
    thread_result = run_codex_thread(
        job,
        args.codex_bin,
        args.cwd,
        args.timeout,
        args.dry_run,
        prompt_override=render_deep_capture_prompt(job, capture_result) if not args.dry_run else None,
        title_override=f"精读｜{clip_title(job, capture_result)[:40]}",
    )
    return {
        "ok": bool(thread_result.get("ok")),
        "mode": "deep_clip",
        "task_level": job_level(job),
        "capture": capture_result,
        "thread": thread_result,
    }


def move_job(path: Path, dest_dir: Path, job: dict[str, Any], status: str) -> Path:
    job["status"] = status
    job["updated_at"] = now_iso()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    write_json(path, job)
    shutil.move(str(path), str(dest))
    return dest


def run_codex(job: dict[str, Any], codex_bin: str, cwd: str, timeout: int, dry_run: bool) -> dict[str, Any]:
    prompt = render_prompt(job)
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{job['job_id']}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.md"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    final_path = run_dir / "final.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "run_dir": str(run_dir),
            "prompt_path": str(prompt_path),
        }

    cmd = [
        codex_bin,
        "exec",
        "--cd",
        cwd,
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "--output-last-message",
        str(final_path),
        "-",
    ]
    env = os.environ.copy()
    env.setdefault("PATH", "/Applications/Codex.app/Contents/Resources:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin")
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        cwd=cwd,
        env=env,
    )
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "run_dir": str(run_dir),
        "prompt_path": str(prompt_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "final_path": str(final_path),
    }


class AppServerClient:
    def __init__(self, codex_bin: str, run_dir: Path):
        self.proc = subprocess.Popen(
            [codex_bin, "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.next_id = 1
        self.stdout_path = run_dir / "app-server.stdout.jsonl"
        self.stderr_path = run_dir / "app-server.stderr.log"
        self.notifications: list[dict[str, Any]] = []

    def close(self) -> None:
        if self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.send_signal(signal.SIGKILL)
            self.proc.wait(timeout=5)

    def send(self, method: str, params: Any | None = None, notify: bool = False) -> int | None:
        if not self.proc.stdin:
            raise RuntimeError("app-server stdin is closed")
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        request_id: int | None = None
        if not notify:
            request_id = self.next_id
            self.next_id += 1
            msg["id"] = request_id
        if params is not None:
            msg["params"] = params
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()
        return request_id

    def _read_line(self, deadline: float) -> dict[str, Any] | None:
        streams = [s for s in (self.proc.stdout, self.proc.stderr) if s]
        while time.monotonic() < deadline:
            if self.proc.poll() is not None and not streams:
                raise RuntimeError(f"app-server exited with code {self.proc.returncode}")
            ready, _, _ = select.select(streams, [], [], 0.2)
            for stream in ready:
                line = stream.readline()
                if not line:
                    streams.remove(stream)
                    continue
                if stream is self.proc.stderr:
                    with self.stderr_path.open("a", encoding="utf-8") as fh:
                        fh.write(line)
                    continue
                with self.stdout_path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return None

    def request(self, method: str, params: Any | None = None, timeout: int = 60) -> dict[str, Any]:
        request_id = self.send(method, params)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._read_line(deadline)
            if msg is None:
                break
            if "id" in msg and msg["id"] == request_id:
                if "error" in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get("result", {})
            if "method" in msg:
                self.notifications.append(msg)
        raise TimeoutError(f"{method} timed out")

    def wait_for_notification(self, method: str, timeout: int) -> dict[str, Any] | None:
        for msg in self.notifications:
            if msg.get("method") == method:
                return msg
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._read_line(deadline)
            if msg is None:
                break
            if "method" in msg:
                self.notifications.append(msg)
                if msg.get("method") == method:
                    return msg
        return None

    def wait_for_turn_done(self, thread_id: str, turn_id: str, timeout: int) -> dict[str, Any] | None:
        for msg in self.notifications:
            if self._is_turn_done(msg, thread_id, turn_id):
                return msg
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._read_line(deadline)
            if msg is None:
                break
            if "method" in msg:
                self.notifications.append(msg)
                if self._is_turn_done(msg, thread_id, turn_id):
                    return msg
        return None

    @staticmethod
    def _is_turn_done(msg: dict[str, Any], thread_id: str, turn_id: str) -> bool:
        method = msg.get("method")
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if method == "turn/completed" and params.get("threadId") == thread_id:
            return True
        if method == "thread/status/changed" and params.get("threadId") == thread_id:
            status = params.get("status") if isinstance(params.get("status"), dict) else {}
            return status.get("type") == "idle"
        if method == "item/completed" and params.get("threadId") == thread_id and params.get("turnId") == turn_id:
            item = params.get("item") if isinstance(params.get("item"), dict) else {}
            return item.get("type") == "agentMessage" and item.get("phase") == "final_answer"
        return False


def run_codex_thread(
    job: dict[str, Any],
    codex_bin: str,
    cwd: str,
    timeout: int,
    dry_run: bool,
    prompt_override: str | None = None,
    title_override: str | None = None,
) -> dict[str, Any]:
    prompt = (AUTOMATION_POLICY + prompt_override) if prompt_override else render_prompt(job)
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{job['job_id']}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "mode": "thread",
            "run_dir": str(run_dir),
            "prompt_path": str(prompt_path),
            "thread_name": title_override or job_title(job),
        }

    client = AppServerClient(codex_bin, run_dir)
    try:
        client.request(
            "initialize",
            {
                "clientInfo": {"name": "wechat-ob-runner", "version": "0.1"},
                "capabilities": {"experimentalApi": True, "requestAttestation": False},
            },
            timeout=30,
        )
        client.send("initialized", notify=True)
        started = client.request(
            "thread/start",
            {
                "cwd": cwd,
                "approvalPolicy": "never",
                "sandbox": "danger-full-access",
                "ephemeral": False,
                "threadSource": "user",
            },
            timeout=60,
        )
        thread = started["thread"]
        thread_id = thread["id"]
        client.request("thread/name/set", {"threadId": thread_id, "name": title_override or job_title(job)}, timeout=30)
        turn = client.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [{"type": "text", "text": prompt, "text_elements": []}],
                "cwd": cwd,
                "approvalPolicy": "never",
                "sandboxPolicy": {"type": "dangerFullAccess"},
            },
            timeout=60,
        )
        turn_id = turn.get("turn", {}).get("id")
        completed = client.wait_for_turn_done(thread_id, turn_id, timeout=timeout)
        return {
            "ok": completed is not None,
            "mode": "thread",
            "thread_id": thread_id,
            "thread_name": title_override or job_title(job),
            "thread_path": thread.get("path"),
            "turn": turn.get("turn"),
            "completed": completed is not None,
            "run_dir": str(run_dir),
            "prompt_path": str(prompt_path),
            "stdout_path": str(client.stdout_path),
            "stderr_path": str(client.stderr_path),
        }
    finally:
        client.close()


def process_one(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    job = load_json(path)
    job["attempts"] = int(job.get("attempts") or 0) + 1
    running_path = move_job(path, RUNNING_DIR, job, "running")

    try:
        if job_level(job) <= 2:
            result = run_clip_job(job, args)
        elif str(job.get("source") or "") != "wechat":
            result = run_deep_clip_job(job, args)
        elif args.mode == "exec":
            result = run_codex(job, args.codex_bin, args.cwd, args.timeout, args.dry_run)
        else:
            result = run_codex_thread(job, args.codex_bin, args.cwd, args.timeout, args.dry_run)
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}

    job["result"] = result
    target_dir = DONE_DIR if result.get("ok") else FAILED_DIR
    final_status = "done" if result.get("ok") else "failed"
    final_path = move_job(running_path, target_dir, job, final_status)
    result["job_path"] = str(final_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pending WeChat Codex jobs.")
    parser.add_argument("--codex-bin", default=DEFAULT_CODEX)
    parser.add_argument("--cwd", default=DEFAULT_CWD)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--mode", choices=["thread", "exec"], default="thread")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    pending = sorted(PENDING_DIR.glob("*.json"))[: args.limit]
    if not pending:
        print(json.dumps({"ok": True, "processed": 0}, ensure_ascii=False))
        return 0

    if args.dry_run:
        results = []
        for path in pending:
            job = load_json(path)
            if job_level(job) <= 2:
                results.append(run_clip_job(job, args))
            elif str(job.get("source") or "") != "wechat":
                results.append(run_deep_clip_job(job, args))
            elif args.mode == "thread":
                results.append(run_codex_thread(job, args.codex_bin, args.cwd, args.timeout, dry_run=True))
            else:
                results.append(run_codex(job, args.codex_bin, args.cwd, args.timeout, dry_run=True))
        print(json.dumps({"ok": True, "processed": len(results), "dry_run": True, "results": results}, ensure_ascii=False, indent=2))
        return 0

    results = [process_one(path, args) for path in pending]
    ok = all(result.get("ok") for result in results)
    print(json.dumps({"ok": ok, "processed": len(results), "results": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
