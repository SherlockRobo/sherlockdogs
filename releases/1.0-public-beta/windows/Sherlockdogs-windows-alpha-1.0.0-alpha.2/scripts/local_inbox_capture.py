#!/usr/bin/env python3
"""Capture local Inbox files as Sherlockdogs clipping items."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR  # noqa: E402

BASE_DIR = CLIPPING_DIR / "local-inbox"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
SUMMARY_COVER_SIZE = (1280, 720)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slug_part(text: str, limit: int = 54) -> str:
    text = clean_text(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-").lower()
    return (text or "local-inbox")[:limit].strip("-")


def digest_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:10]


def path_from_file_url(value: str) -> str:
    if value.startswith("file://"):
        return value[7:]
    return value


def title_from_payload(payload: dict[str, Any], fallback: str) -> str:
    title = clean_text(str(payload.get("title") or fallback or ""))
    if title:
        return title[:100]
    text = clean_text(str(payload.get("text") or ""))
    if text:
        return text[:80]
    files = payload.get("files") if isinstance(payload.get("files"), list) else []
    if files:
        return clean_text(str(files[0].get("name") or "本地文件剪藏"))[:80]
    return "本地 Inbox 剪藏"


def safe_filename(name: str, fallback: str) -> str:
    stem = slug_part(Path(name).stem or fallback, 40) or fallback
    suffix = Path(name).suffix.lower()
    return f"{stem}{suffix}"


def unique_asset_path(assets_dir: Path, filename: str) -> Path:
    path = assets_dir / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for idx in range(2, 1000):
        candidate = assets_dir / f"{stem}-{idx}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"cannot create unique asset path for {filename}")


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image

        with Image.open(path) as img:
            return img.size
    except Exception:
        pass
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


def video_metadata(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return {"duration": "", "duration_seconds": None, "status": "missing-ffprobe"}
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration,size,bit_rate",
        "-show_entries",
        "stream=codec_type,width,height",
        "-of",
        "json",
        str(path),
    ]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=10, check=False)
    except Exception as exc:
        return {"duration": "", "duration_seconds": None, "status": f"ffprobe-error: {exc}"}
    if proc.returncode != 0:
        return {"duration": "", "duration_seconds": None, "status": clean_text(proc.stderr or proc.stdout)[:120]}
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        return {"duration": "", "duration_seconds": None, "status": "ffprobe-non-json"}
    duration_seconds = None
    try:
        duration_seconds = int(float(payload.get("format", {}).get("duration")))
    except Exception:
        pass
    width = height = 0
    for stream in payload.get("streams") or []:
        if stream.get("codec_type") == "video":
            width = int(stream.get("width") or 0)
            height = int(stream.get("height") or 0)
            break
    return {
        "duration": format_duration(duration_seconds),
        "duration_seconds": duration_seconds,
        "width": width,
        "height": height,
        "status": "ok" if duration_seconds is not None else "missing-duration",
    }


def format_duration(seconds: Any) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return ""
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def cost_hint(kind: str, duration_seconds: Any) -> str:
    if kind != "video":
        return "低：本地文件"
    try:
        total = int(duration_seconds)
    except (TypeError, ValueError):
        return "未知：本地视频未识别时长"
    if total <= 60:
        return "低：短视频，适合 #3/#4"
    if total <= 10 * 60:
        return "中：建议先 #3，再决定 #4"
    if total <= 30 * 60:
        return "高：建议先 #3 看章节/字幕"
    return "很高：建议 #3 预检后再 #4/#5"


def load_font(size: int, bold: bool = False) -> Any:
    try:
        from PIL import ImageFont

        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for path in candidates:
            if Path(path).exists():
                return ImageFont.truetype(path, size=size)
        return ImageFont.load_default()
    except Exception:
        return None


def text_width(draw: Any, text: str, font: Any) -> int:
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0])
    except Exception:
        return len(text) * 16


def wrap_by_width(draw: Any, text: str, font: Any, max_width: int, max_lines: int) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = char
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and text_width(draw, "".join(lines), font) < text_width(draw, text, font):
        lines[-1] = lines[-1].rstrip("，。,. ") + "..."
    return lines


def generate_summary_cover(assets_dir: Path, title: str, description: str, kind: str, duration: str) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:
        return {"ok": False, "status": f"summary-cover-failed: {exc}"}

    assets_dir.mkdir(parents=True, exist_ok=True)
    width, height = SUMMARY_COVER_SIZE
    image = Image.new("RGB", (width, height), "#111111")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        shade = int(250 - y / height * 24)
        draw.line([(0, y), (width, y)], fill=(shade, shade, shade))

    accent = "#f4b400"
    title_font = load_font(58, bold=True)
    body_font = load_font(34)
    meta_font = load_font(28, bold=True)
    small_font = load_font(24)

    label = {"text": "TEXT", "video": "VIDEO", "document": "DOC", "bundle": "BUNDLE", "file": "FILE"}.get(kind, kind.upper())
    draw.rounded_rectangle((72, 64, 252, 116), radius=20, fill=accent)
    draw.text((104, 78), label, fill="#111111", font=meta_font)
    if duration:
        draw.rounded_rectangle((278, 64, 436, 116), radius=20, outline="#111111", width=2)
        draw.text((306, 78), duration, fill="#111111", font=meta_font)

    title_lines = wrap_by_width(draw, title, title_font, 1040, 3)
    y = 168
    for line in title_lines:
        draw.text((72, y), line, fill="#111111", font=title_font)
        y += 72

    desc = description or "已保存到 Sherlockdogs 本地 Inbox，等待后续解析。"
    y += 26
    for line in wrap_by_width(draw, desc, body_font, 980, 4):
        draw.text((76, y), line, fill="#374151", font=body_font)
        y += 48

    draw.line((72, height - 116, width - 72, height - 116), fill="#d1d5db", width=2)
    draw.text((72, height - 82), "Sherlockdogs", fill="#111111", font=meta_font)
    draw.text((270, height - 78), "本地 Inbox · 私人图书馆 · 直接进 Codex", fill="#4b5563", font=small_font)

    filename = f"{slug_part(title, 40) or 'local-inbox'}-summary-{digest_text(title + description)}.png"
    path = assets_dir / filename
    image.save(path)
    return {
        "ok": True,
        "kind": "summary-cover",
        "local": f"assets/{filename}",
        "source": "generated-summary-cover",
        "content_type": "image/png",
        "bytes": path.stat().st_size,
    }


def copy_file_asset(file_info: dict[str, Any], assets_dir: Path, index: int) -> dict[str, Any]:
    source_path = Path(path_from_file_url(str(file_info.get("path") or "")))
    if not source_path.exists() or not source_path.is_file():
        return {"ok": False, "status": "source-not-found", "source": str(source_path)}
    assets_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_filename(str(file_info.get("name") or source_path.name), f"asset-{index}")
    dest = unique_asset_path(assets_dir, filename)
    shutil.copy2(source_path, dest)
    kind = str(file_info.get("kind") or "file")
    mime = str(file_info.get("mime") or mimetypes.guess_type(str(dest))[0] or "")
    asset: dict[str, Any] = {
        "ok": True,
        "kind": kind,
        "local": f"assets/{dest.name}",
        "source": str(source_path),
        "content_type": mime,
        "bytes": dest.stat().st_size,
        "original_name": source_path.name,
    }
    if dest.suffix.lower() in IMAGE_SUFFIXES:
        width, height = image_dimensions(dest)
        asset.update({"kind": "image", "width": width, "height": height})
    elif dest.suffix.lower() in VIDEO_SUFFIXES:
        meta = video_metadata(dest)
        asset.update({"kind": "video", **meta})
    return asset


def markdown_frontmatter(metadata: dict[str, Any], task: str) -> str:
    def js(value: Any) -> str:
        return json.dumps("" if value is None else str(value), ensure_ascii=False)

    return "\n".join(
        [
            "---",
            'source: "local-inbox"',
            "type: local_inbox_raw",
            f"url: {js(metadata.get('url'))}",
            f"title: {js(metadata.get('title'))}",
            f"captured_at: {js(metadata.get('captured_at'))}",
            f"task: {js(task)}",
            f"asset_count: {int(metadata.get('asset_count') or 0)}",
            "tags:",
            "  - local-inbox",
            "  - sherlockdogs",
            "---",
            "",
        ]
    )


def capture(job: dict[str, Any], task: str, job_id: str) -> dict[str, Any]:
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    payload = extra.get("payload") if isinstance(extra.get("payload"), dict) else {}
    title = title_from_payload(payload, str(extra.get("title") or ""))
    kind = str(payload.get("kind") or "file")
    text = str(payload.get("text") or "").strip()
    urls = payload.get("urls") if isinstance(payload.get("urls"), list) else []
    files = payload.get("files") if isinstance(payload.get("files"), list) else []
    stamp = datetime.now().strftime("%Y%m%d")
    digest = digest_text(json.dumps(payload, ensure_ascii=False, sort_keys=True)[:5000] + str(job.get("url") or ""))
    item_dir = BASE_DIR / f"{stamp}-{slug_part(title)}-{digest}"
    assets_dir = item_dir / "assets"
    item_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, Any]] = []
    for idx, file_info in enumerate(files, start=1):
        if not isinstance(file_info, dict):
            continue
        asset = copy_file_asset(file_info, assets_dir, idx)
        if asset.get("ok"):
            assets.append({key: value for key, value in asset.items() if key != "ok"})

    duration = next((str(asset.get("duration") or "") for asset in assets if asset.get("kind") == "video"), "")
    duration_seconds = next((asset.get("duration_seconds") for asset in assets if asset.get("kind") == "video"), None)
    description = clean_text(text)[:220] if text else ""
    if not description:
        description = "、".join(str(asset.get("original_name") or "") for asset in assets[:3] if asset.get("original_name"))
    if not any(asset.get("kind") in {"image", "summary-cover"} for asset in assets):
        summary = generate_summary_cover(assets_dir, title, description, kind, duration)
        if summary.get("ok"):
            assets.insert(0, {key: value for key, value in summary.items() if key != "ok"})

    raw_path = item_dir / "raw.md"
    metadata_path = item_dir / "metadata.json"
    image_count = sum(1 for asset in assets if asset.get("kind") in {"image", "summary-cover"})
    metadata = {
        "title": title,
        "account": "本地 Inbox",
        "source": "local-inbox",
        "kind": kind,
        "url": str(job.get("url") or ""),
        "urls": urls,
        "primary_url": str(payload.get("primary_url") or (urls[0] if urls else "")),
        "description": description or "本地 Inbox 剪藏，已保存到私人图书馆。",
        "duration": duration,
        "duration_seconds": duration_seconds,
        "processing_cost_hint": cost_hint("video" if any(asset.get("kind") == "video" for asset in assets) else kind, duration_seconds),
        "assets": assets,
        "asset_count": image_count,
        "file_count": len(assets),
        "payload": payload,
        "captured_at": now_iso(),
        "job_id": job_id,
        "article_dir": str(item_dir),
        "raw_path": str(raw_path),
    }

    raw_lines = [
        markdown_frontmatter(metadata, task),
        f"# {title}",
        "",
        "## 收件状态",
        "",
        "已从 Sherlockdogs 本地 Inbox 入库。当前阶段只做本地保存和轻量 metadata，不做深解析。",
        "",
    ]
    if urls:
        raw_lines.extend(["## 链接", ""])
        raw_lines.extend(f"- {url}" for url in urls)
        raw_lines.append("")
    if text:
        raw_lines.extend(["## 文字", "", text, ""])
    if assets:
        raw_lines.extend(["## 附件", "", "| 文件 | 类型 | 大小 |", "|---|---|---|"])
        for asset in assets:
            raw_lines.append(f"| [{asset.get('original_name') or Path(str(asset.get('local'))).name}]({asset.get('local')}) | {asset.get('kind')} | {asset.get('bytes', 0)} |")
        raw_lines.append("")
    image_assets = [asset for asset in assets if asset.get("kind") in {"image", "summary-cover"}]
    if image_assets:
        raw_lines.extend(["## 图片预览", ""])
        raw_lines.extend(f"![]({asset['local']})" for asset in image_assets[:6])
        raw_lines.append("")

    raw_path.write_text("\n".join(raw_lines), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "source": "local_inbox",
        "article_dir": str(item_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "asset_count": image_count,
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a Sherlockdogs local Inbox job.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--job-file", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    job = json.loads(Path(args.job_file).read_text(encoding="utf-8"))
    result = capture(job, task=args.task, job_id=args.job_id)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["raw_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
