from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>'\"）)]+")
TASK_LINE_RE = re.compile(r"(?im)^\s*(#(?:[1-5]\b.*|ob\b.*|))\s*$")
TASK_INLINE_RE = re.compile(r"(?<!\w)#(?:[1-5]\b[^\n]*|ob\b[^\n]*|)(?=\s|$)")


@dataclass(frozen=True)
class ParsedInput:
    text: str
    urls: list[str]
    task: str
    task_level: int
    source: str
    title: str


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_url(url: str) -> str:
    return url.rstrip(".,，。;；!！?？)]}」』”")


def classify_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "mp.weixin.qq.com" in host:
        return "wechat"
    if host in {"x.com", "twitter.com"} or host.endswith(".x.com") or host.endswith(".twitter.com"):
        return "x"
    if "xiaohongshu.com" in host or "xhslink.com" in host:
        return "xhs"
    if "bilibili.com" in host or "b23.tv" in host:
        return "bilibili"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "tiktok.com" in host:
        return "tiktok"
    if "douyin.com" in host:
        return "douyin"
    return "web"


def parse_task(text: str) -> tuple[int, str]:
    line_matches = TASK_LINE_RE.findall(text or "")
    inline_matches = TASK_INLINE_RE.findall(text or "")
    raw = (line_matches or inline_matches or [""])[-1].strip()
    if raw in {"", "#1"}:
        return 1, "#1"
    if raw == "#":
        return 2, "#2"
    if raw.startswith("#ob"):
        return 4, raw
    match = re.match(r"#([1-5])\b", raw)
    if match:
        return int(match.group(1)), raw
    return 1, "#1"


def strip_task_lines(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if TASK_LINE_RE.match(line.strip()):
            continue
        lines.append(TASK_INLINE_RE.sub("", line).rstrip())
    return "\n".join(lines).strip()


def title_hint(text: str, url: str) -> str:
    stripped = strip_task_lines(text)
    for line in stripped.splitlines():
        line = line.strip()
        if line and not line.startswith("http"):
            return line[:120]
    parsed = urlparse(url)
    return parsed.netloc or "clipping"


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", value.lower()).strip("-")
    return value[:80] or "clipping"


def parse_input(text: str) -> ParsedInput:
    urls = []
    for match in URL_RE.findall(text or ""):
        url = clean_url(match)
        if url not in urls:
            urls.append(url)
    task_level, task = parse_task(text)
    primary_url = urls[0] if urls else "local://text"
    source = classify_url(primary_url) if urls else "text"
    return ParsedInput(
        text=strip_task_lines(text),
        urls=urls,
        task=task,
        task_level=task_level,
        source=source,
        title=title_hint(text, primary_url),
    )


def write_ingest(text: str, vault: Path) -> dict:
    parsed = parse_input(text)
    digest_body = "\n".join(parsed.urls) + "\n" + parsed.text
    digest = hashlib.sha1(digest_body.encode("utf-8", errors="replace")).hexdigest()[:10]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = f"{datetime.now().strftime('%Y%m%d')}-{parsed.source}-{slugify(parsed.title)}-{digest}"
    item_dir = vault / "clipping" / parsed.source / slug
    item_dir.mkdir(parents=True, exist_ok=True)

    raw_path = item_dir / "raw.md"
    metadata_path = item_dir / "metadata.json"
    raw_path.write_text(
        f"# {parsed.title}\n\n"
        f"- source: {parsed.source}\n"
        f"- task: {parsed.task}\n"
        f"- captured_at: {now_iso()}\n\n"
        f"## Input\n\n{parsed.text}\n\n"
        f"## URLs\n\n" + "\n".join(f"- {url}" for url in parsed.urls) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "title": parsed.title,
        "source": parsed.source,
        "urls": parsed.urls,
        "task": parsed.task,
        "task_level": parsed.task_level,
        "captured_at": now_iso(),
        "archive_dir": str(item_dir),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    job = None
    if parsed.task_level >= 2:
        jobs_dir = vault / "jobs" / "pending"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job = {
            "job_id": f"{stamp}-{parsed.source}-{digest}",
            "status": "pending",
            "source": parsed.source,
            "task": parsed.task,
            "task_level": parsed.task_level,
            "title": parsed.title,
            "urls": parsed.urls,
            "archive_dir": str(item_dir),
            "raw_path": str(raw_path),
            "created_at": now_iso(),
        }
        job_path = jobs_dir / f"{job['job_id']}.json"
        job_path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        job["job_path"] = str(job_path)

    return {
        "ok": True,
        "archive_dir": str(item_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "job": job,
    }
