#!/usr/bin/env python3
"""Store a media/social URL as a link-only clipping item.

This intentionally does not parse, transcribe, or download the target media.
It only performs lightweight metadata preflight: duration and cover image.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import parse_qs, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR  # noqa: E402

BASE_DIR = CLIPPING_DIR
SOURCE_DIRS = {
    "xhs": BASE_DIR / "xhs",
    "bilibili": BASE_DIR / "bilibili",
    "youtube": BASE_DIR / "youtube",
    "tiktok": BASE_DIR / "tiktok",
    "douyin": BASE_DIR / "douyin",
}
SOURCE_LABELS = {
    "xhs": "小红书",
    "bilibili": "B站",
    "youtube": "YouTube",
    "tiktok": "TikTok",
    "douyin": "抖音",
}
DURATION_TIMEOUT = 25
COVER_TIMEOUT = 8
MAX_COVER_BYTES = 8 * 1024 * 1024
DOUYIN_HTML_TIMEOUT = 15
XHS_HTML_TIMEOUT = 15
MAX_PREVIEW_ASSETS = 3
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
    return (text or "media-link")[:limit].strip("-")


def url_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def format_duration(seconds: Any) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return ""
    if total < 0:
        return ""
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def cost_hint(seconds: Any) -> str:
    try:
        total = int(float(seconds))
    except (TypeError, ValueError):
        return "未知：需要 #3 预检"
    if total <= 60:
        return "低：短内容，适合 #3/#4"
    if total <= 10 * 60:
        return "中：建议先 #3，再决定 #4"
    if total <= 30 * 60:
        return "高：建议先 #3 看字幕/章节"
    return "很高：建议 #3 预检后再 #4/#5"


def best_thumbnail(payload: dict[str, Any]) -> str:
    thumbnail = clean_text(str(payload.get("thumbnail") or ""))
    if thumbnail.startswith(("http://", "https://")):
        return thumbnail
    candidates = payload.get("thumbnails")
    if not isinstance(candidates, list):
        return ""
    ranked: list[tuple[int, str]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        url = clean_text(str(item.get("url") or ""))
        if not url.startswith(("http://", "https://")):
            continue
        width = item.get("width") or 0
        height = item.get("height") or 0
        try:
            score = int(width) * int(height)
        except (TypeError, ValueError):
            score = 0
        ranked.append((score, url))
    if not ranked:
        return ""
    ranked.sort(reverse=True)
    return ranked[0][1]


def cover_extension(url: str, content_type: str) -> str:
    guessed = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    if guessed in {".jpe", ".jpeg", ".jpg", ".png", ".webp"}:
        return ".jpg" if guessed in {".jpe", ".jpeg"} else guessed
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def download_cover(thumbnail_url: str, assets_dir: Path, stem: str) -> dict[str, Any]:
    if not thumbnail_url:
        return {"ok": False, "status": "missing-thumbnail-url"}
    assets_dir.mkdir(parents=True, exist_ok=True)
    request = Request(
        thumbnail_url,
        headers={
            "User-Agent": "Mozilla/5.0 Sherlockdogs/1.5",
            "Referer": "https://www.google.com/",
        },
    )
    last_error = ""
    data = b""
    content_type = ""
    for _ in range(2):
        try:
            with urlopen(request, timeout=COVER_TIMEOUT) as response:
                content_type = response.headers.get("content-type", "")
                data = response.read(MAX_COVER_BYTES + 1)
            break
        except URLError as exc:
            last_error = str(exc)
        except Exception as exc:
            last_error = str(exc)
    else:
        curl_path = shutil.which("curl")
        if not curl_path:
            return {"ok": False, "status": f"download-failed: {last_error}"}
        tmp_path = assets_dir / f".tmp-cover-{url_hash(thumbnail_url)}"
        curl_cmd = [
            curl_path,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--connect-timeout",
            str(COVER_TIMEOUT),
            "--max-time",
            str(max(COVER_TIMEOUT * 2, 16)),
            "--retry",
            "2",
            "--retry-delay",
            "1",
            "-A",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "-H",
            "Referer: https://www.douyin.com/",
            thumbnail_url,
            "-o",
            str(tmp_path),
        ]
        try:
            proc = subprocess.run(curl_cmd, text=True, capture_output=True, timeout=max(COVER_TIMEOUT * 3, 24), check=False)
            if proc.returncode != 0:
                tmp_path.unlink(missing_ok=True)
                error = clean_text(proc.stderr or proc.stdout)[:160]
                return {"ok": False, "status": f"download-failed: {last_error}; curl-failed: {error}"}
            if tmp_path.stat().st_size > MAX_COVER_BYTES:
                tmp_path.unlink(missing_ok=True)
                return {"ok": False, "status": "cover-too-large"}
            data = tmp_path.read_bytes()
            content_type = mimetypes.guess_type(str(tmp_path))[0] or ""
            tmp_path.unlink(missing_ok=True)
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            return {"ok": False, "status": f"download-failed: {last_error}; curl-error: {exc}"}
    if len(data) > MAX_COVER_BYTES:
        return {"ok": False, "status": "cover-too-large"}
    ext = cover_extension(thumbnail_url, content_type)
    filename = f"{slug_part(stem, 40) or 'media'}-cover-{url_hash(thumbnail_url)}{ext}"
    path = assets_dir / filename
    path.write_bytes(data)
    return {
        "ok": True,
        "status": "ok",
        "local": f"assets/{filename}",
        "source": thumbnail_url,
        "content_type": content_type,
        "bytes": len(data),
    }


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


def generate_summary_cover(
    assets_dir: Path,
    source: str,
    title: str,
    description: str,
    duration: str,
    stem: str,
) -> dict[str, Any]:
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:
        return {"ok": False, "status": f"summary-cover-failed: {exc}"}

    assets_dir.mkdir(parents=True, exist_ok=True)
    width, height = SUMMARY_COVER_SIZE
    image = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(image)

    # A simple XHS-friendly editorial card: readable first, decorative second.
    for y in range(height):
        shade = int(17 + y / height * 22)
        draw.line([(0, y), (width, y)], fill=(shade, shade + 8, shade + 18))

    accent = "#f7c948"
    source_label = SOURCE_LABELS.get(source, source.upper())
    title_font = load_font(56, bold=True)
    body_font = load_font(34)
    meta_font = load_font(28, bold=True)
    small_font = load_font(24)

    draw.rounded_rectangle((72, 64, 288, 116), radius=22, fill=accent)
    draw.text((104, 78), source_label, fill="#111827", font=meta_font)
    if duration:
        draw.rounded_rectangle((314, 64, 472, 116), radius=22, outline="#e5e7eb", width=2)
        draw.text((342, 78), duration, fill="#f9fafb", font=meta_font)

    title_lines = wrap_by_width(draw, title.replace(f"{source_label}｜", ""), title_font, 1040, 3)
    y = 164
    for line in title_lines:
        draw.text((72, y), line, fill="#f9fafb", font=title_font)
        y += 72

    desc = description or "已保存到 Sherlockdogs，等待后续解析。"
    desc_lines = wrap_by_width(draw, desc, body_font, 1000, 4)
    y += 28
    for line in desc_lines:
        draw.text((76, y), line, fill="#d1d5db", font=body_font)
        y += 48

    draw.line((72, height - 116, width - 72, height - 116), fill="#374151", width=2)
    draw.text((72, height - 82), "Sherlockdogs", fill="#f9fafb", font=meta_font)
    draw.text((270, height - 78), "本地入库 · 直接进 Codex 对话 · 后续可 #3/#4/#5", fill="#9ca3af", font=small_font)

    filename = f"{slug_part(stem, 40) or 'media'}-summary-{url_hash(title + description)}.png"
    path = assets_dir / filename
    image.save(path)
    return {
        "ok": True,
        "status": "generated-summary-cover",
        "local": f"assets/{filename}",
        "source": "generated-summary-cover",
        "content_type": "image/png",
        "bytes": path.stat().st_size,
    }


def decode_js_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value


def probe_douyin_public_html(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "Referer": "https://www.douyin.com/",
        },
    )
    try:
        with urlopen(request, timeout=DOUYIN_HTML_TIMEOUT) as response:
            text = response.read(2_000_000).decode("utf-8", errors="replace")
    except Exception as exc:
        return {"ok": False, "status": f"html-failed: {exc}"}

    normalized = html.unescape(text).replace("\\u002F", "/").replace("\\/", "/")
    description = ""
    meta_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
        normalized,
        flags=re.I,
    )
    if meta_match:
        description = clean_text(html.unescape(meta_match.group(1)))
    desc_match = re.search(r'"desc"\s*:\s*"((?:\\.|[^"\\])*)"', normalized)
    if desc_match:
        description = clean_text(decode_js_string(desc_match.group(1))) or description

    image_urls = re.findall(r'https?://[^\s"\'<>]+?\.(?:jpg|jpeg|png|webp)[^\s"\'<>]*', normalized, flags=re.I)
    thumbnail_url = next((u for u in image_urls if "douyinpic.com" in u and "logo" not in u.lower()), "")
    if not thumbnail_url and image_urls:
        thumbnail_url = image_urls[0]

    duration_candidates: list[int] = []
    for match in re.findall(r'"duration"\s*:\s*(\d+)', normalized):
        try:
            duration_candidates.append(int(match))
        except ValueError:
            pass
    duration_seconds = None
    if duration_candidates:
        largest = max(duration_candidates)
        duration_seconds = int(round(largest / 1000)) if largest > 10000 else largest

    return {
        "ok": bool(thumbnail_url or description or duration_seconds is not None),
        "status": "ok",
        "description": description,
        "thumbnail_url": thumbnail_url,
        "duration_seconds": duration_seconds,
    }


def probe_xhs_public_html(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
            "Referer": "https://www.xiaohongshu.com/",
        },
    )
    try:
        with urlopen(request, timeout=XHS_HTML_TIMEOUT) as response:
            text = response.read(2_000_000).decode("utf-8", errors="replace")
    except Exception as exc:
        return {"ok": False, "status": f"html-failed: {exc}"}

    normalized = html.unescape(text).replace("\\u002F", "/").replace("\\/", "/")
    description = ""
    desc_match = re.search(r'"desc"\s*:\s*"((?:\\.|[^"\\])*)"', normalized)
    if desc_match:
        description = clean_text(decode_js_string(desc_match.group(1)))

    image_urls: list[str] = []
    for candidate in re.findall(r'https?://[^\s"\'<>]+', normalized):
        if "xhscdn.com" not in candidate:
            continue
        if "notes_pre_post" not in candidate and "imageView" not in candidate:
            continue
        candidate = candidate.rstrip("\\,]} ")
        if candidate not in image_urls:
            image_urls.append(candidate)
        if len(image_urls) >= MAX_PREVIEW_ASSETS:
            break

    return {
        "ok": bool(image_urls or description),
        "status": "ok",
        "description": description,
        "thumbnail_url": image_urls[0] if image_urls else "",
        "image_urls": image_urls,
    }


def runnable(cmd: list[str]) -> bool:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=5, check=False)
    except Exception:
        return False
    return proc.returncode == 0


def resolve_ytdlp_command() -> list[str]:
    binary = shutil.which("yt-dlp")
    if binary:
        return [binary]
    for python_bin in ("/opt/homebrew/bin/python3", sys.executable, "/usr/bin/python3"):
        if python_bin and Path(python_bin).exists() and runnable([python_bin, "-m", "yt_dlp", "--version"]):
            return [python_bin, "-m", "yt_dlp"]
    return []


def run_ytdlp_metadata(cmd: list[str], url: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    args = cmd + ["--skip-download", "--no-warnings", "--dump-json", "--no-playlist"]
    if extra_args:
        args.extend(extra_args)
    args.append(url)
    return subprocess.run(
        args,
        text=True,
        capture_output=True,
        timeout=DURATION_TIMEOUT,
        check=False,
    )


def probe_duration(url: str) -> dict[str, Any]:
    cmd = resolve_ytdlp_command()
    if not cmd:
        return {
            "duration_seconds": None,
            "duration": "",
            "duration_status": "missing-yt-dlp",
            "processing_cost_hint": "未知：未安装 yt-dlp",
            "thumbnail_url": "",
            "thumbnail_status": "missing-yt-dlp",
        }
    try:
        proc = run_ytdlp_metadata(cmd, url)
        if proc.returncode != 0 and "Fresh cookies" in (proc.stderr or proc.stdout):
            proc = run_ytdlp_metadata(cmd, url, ["--cookies-from-browser", "chrome"])
    except subprocess.TimeoutExpired:
        return {
            "duration_seconds": None,
            "duration": "",
            "duration_status": "timeout",
            "processing_cost_hint": "未知：时长预检超时",
            "thumbnail_url": "",
            "thumbnail_status": "timeout",
        }
    except Exception as exc:
        return {
            "duration_seconds": None,
            "duration": "",
            "duration_status": f"error: {exc}",
            "processing_cost_hint": "未知：时长预检失败",
            "thumbnail_url": "",
            "thumbnail_status": "error",
        }
    if proc.returncode != 0:
        error = clean_text(proc.stderr or proc.stdout)[:180]
        return {
            "duration_seconds": None,
            "duration": "",
            "duration_status": f"yt-dlp-failed: {error}",
            "processing_cost_hint": "未知：平台未返回时长",
            "thumbnail_url": "",
            "thumbnail_status": "yt-dlp-failed",
        }
    try:
        payload = json.loads(proc.stdout.splitlines()[0])
    except Exception:
        return {
            "duration_seconds": None,
            "duration": "",
            "duration_status": "non-json",
            "processing_cost_hint": "未知：时长预检输出异常",
            "thumbnail_url": "",
            "thumbnail_status": "non-json",
        }
    duration_seconds = payload.get("duration")
    thumbnail_url = best_thumbnail(payload)
    return {
        "duration_seconds": duration_seconds,
        "duration": format_duration(duration_seconds),
        "duration_status": "ok" if duration_seconds is not None else "missing-duration",
        "processing_cost_hint": cost_hint(duration_seconds),
        "thumbnail_url": thumbnail_url,
        "thumbnail_status": "ok" if thumbnail_url else "missing-thumbnail",
    }


def source_from_url(url: str) -> str:
    lowered = url.lower()
    if re.search(r"https?://([^/]+\.)?(xiaohongshu\.com|xhslink\.com)/", lowered):
        return "xhs"
    if re.search(r"https?://([^/]+\.)?(bilibili\.com|b23\.tv)/", lowered):
        return "bilibili"
    if re.search(r"https?://([^/]+\.)?(youtube\.com|youtu\.be)/", lowered):
        return "youtube"
    if re.search(r"https?://([^/]+\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/", lowered):
        return "tiktok"
    if re.search(r"https?://([^/]+\.)?(douyin\.com|v\.douyin\.com|iesdouyin\.com)/", lowered):
        return "douyin"
    return "media"


def clean_title_hint(title_hint: str, url: str) -> str:
    title = clean_text(title_hint)
    title = title.replace(url, "").strip(" -_|｜\n\t")
    if not title or title.startswith(("http://", "https://")):
        return ""
    return title[:120]


def title_for(url: str, source: str, title_hint: str = "") -> str:
    parsed = urlparse(url)
    label = SOURCE_LABELS.get(source, "Media")
    hint = clean_title_hint(title_hint, url)
    if hint:
        return f"{label}｜{hint}"
    parts = [part for part in parsed.path.split("/") if part]
    if source == "youtube":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        topic = video_id or (parts[0] if parts else "")
    elif source == "bilibili":
        topic = next((part for part in parts if part.upper().startswith("BV")), "") or (parts[-1] if parts else "")
    elif source == "tiktok":
        topic = "/".join(parts[-3:]) if parts else parsed.netloc
    elif source == "douyin":
        topic = "/".join(parts[-3:]) if parts else parsed.netloc
    elif source == "xhs":
        topic = "/".join(parts[-2:]) if parts else parsed.netloc
    else:
        topic = parsed.path.strip("/") or parsed.netloc
    return f"{label}｜{(topic or url_hash(url))[:80]}"


def markdown_frontmatter(metadata: dict[str, Any], task: str) -> str:
    def js(value: Any) -> str:
        return json.dumps("" if value is None else str(value), ensure_ascii=False)

    return "\n".join(
        [
            "---",
            f"source: {metadata.get('source')}",
            "type: media_link_raw",
            f"source_id: {js(metadata.get('source_id'))}",
            f"url: {js(metadata.get('url'))}",
            f"title: {js(metadata.get('title'))}",
            f"account: {js(metadata.get('account'))}",
            f"author: {js(metadata.get('author'))}",
            f"published_at: {js(metadata.get('published_at'))}",
            f"captured_at: {js(metadata.get('captured_at'))}",
            f"task: {js(task)}",
            f"asset_count: {int(metadata.get('asset_count') or 0)}",
            "status: link_only",
            "tags:",
            f"  - {metadata.get('source')}-inbox",
            "  - media-link",
            "---",
            "",
        ]
    )


def capture(url: str, task: str, job_id: str, out_base: Path | None = None, title_hint: str = "") -> dict[str, Any]:
    source = source_from_url(url)
    out_dir = out_base or SOURCE_DIRS.get(source) or (BASE_DIR / source)
    title = title_for(url, source, title_hint=title_hint)
    clean_hint = clean_title_hint(title_hint, url)
    description = clean_hint or "仅保存链接；视频/图文解析将在 Codex 对话中按 #3/#4/#5 执行。"
    public_fallback: dict[str, Any] = {}
    if source == "xhs":
        duration_info = {
            "duration_seconds": None,
            "duration": "",
            "duration_status": "not-video-or-unavailable",
            "processing_cost_hint": "未知：平台未返回时长",
            "thumbnail_url": "",
            "thumbnail_status": "html-fallback-pending",
        }
    else:
        duration_info = probe_duration(url)
    if source == "douyin" and (
        not duration_info.get("thumbnail_url") or duration_info.get("duration_seconds") is None
    ):
        public_fallback = probe_douyin_public_html(url)
        fallback_duration = public_fallback.get("duration_seconds")
        if duration_info.get("duration_seconds") is None and fallback_duration is not None:
            duration_info["duration_seconds"] = fallback_duration
            duration_info["duration"] = format_duration(fallback_duration)
            duration_info["duration_status"] = "ok-html-fallback"
            duration_info["processing_cost_hint"] = cost_hint(fallback_duration)
        if not duration_info.get("thumbnail_url") and public_fallback.get("thumbnail_url"):
            duration_info["thumbnail_url"] = public_fallback["thumbnail_url"]
            duration_info["thumbnail_status"] = "ok-html-fallback"
        if public_fallback.get("description"):
            description = clean_text(public_fallback["description"])
    elif source == "xhs":
        public_fallback = probe_xhs_public_html(url)
        if public_fallback.get("thumbnail_url"):
            duration_info["thumbnail_url"] = public_fallback["thumbnail_url"]
            duration_info["thumbnail_status"] = "ok-html-fallback"
        if public_fallback.get("description"):
            description = clean_text(public_fallback["description"])
    slug = f"{datetime.now().strftime('%Y%m%d')}-{slug_part(title)}-{url_hash(url)}"
    item_dir = out_dir / slug
    item_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = item_dir / "assets"
    assets: list[dict[str, Any]] = []
    cover_result: dict[str, Any] = {"ok": False, "status": "missing-thumbnail-url"}
    image_urls = []
    if isinstance(public_fallback.get("image_urls"), list):
        image_urls = [str(item) for item in public_fallback["image_urls"] if item]
    if not image_urls and duration_info.get("thumbnail_url"):
        image_urls = [str(duration_info["thumbnail_url"])]
    for index, image_url in enumerate(image_urls[:MAX_PREVIEW_ASSETS], start=1):
        result = download_cover(image_url, assets_dir, title if index == 1 else f"{title}-{index:02d}")
        if index == 1:
            cover_result = result
        if result.get("ok"):
            assets.append(
                {
                    "kind": "cover" if index == 1 else "image",
                    "local": result["local"],
                    "source": result["source"],
                    "content_type": result.get("content_type") or "",
                    "bytes": result.get("bytes") or 0,
                }
            )
    if not assets:
        result = generate_summary_cover(
            assets_dir=assets_dir,
            source=source,
            title=title,
            description=description,
            duration=duration_info["duration"],
            stem=title,
        )
        if result.get("ok"):
            cover_result = result
            assets.append(
                {
                    "kind": "summary-cover",
                    "local": result["local"],
                    "source": result["source"],
                    "content_type": result.get("content_type") or "",
                    "bytes": result.get("bytes") or 0,
                }
            )

    cover_local = cover_result.get("local") or (assets[0].get("local") if assets else "")
    cover_source = cover_result.get("source") or (assets[0].get("source") if assets else duration_info.get("thumbnail_url") or "")
    cover_status = cover_result.get("status") or ("ok" if assets else "missing-thumbnail")

    metadata = {
        "source": source,
        "source_id": url_hash(url),
        "url": url,
        "canonical_url": url,
        "title": title,
        "account": "",
        "author": "",
        "description": description,
        "inbox_title": clean_hint,
        "duration_seconds": duration_info["duration_seconds"],
        "duration": duration_info["duration"],
        "duration_status": duration_info["duration_status"],
        "processing_cost_hint": duration_info["processing_cost_hint"],
        "thumbnail_url": duration_info.get("thumbnail_url") or "",
        "thumbnail_status": duration_info.get("thumbnail_status") or "",
        "public_fallback_status": public_fallback.get("status") or "",
        "cover": cover_local,
        "cover_source": cover_source,
        "cover_status": cover_status,
        "published_at": "",
        "captured_at": now_iso(),
        "job_id": job_id,
        "slug": slug,
        "article_dir": str(item_dir),
        "raw_path": str(item_dir / "raw.md"),
        "capture_method": "link-only",
        "parse_policy": "defer-to-codex",
        "asset_count": len(assets),
        "assets": assets,
    }

    raw_path = item_dir / "raw.md"
    metadata_path = item_dir / "metadata.json"
    raw_lines = [
        markdown_frontmatter(metadata, task),
        f"# {title}",
        "",
        f"[原始链接]({url})",
        "",
        "## 收件状态",
        "",
        "已保存链接、标题、时长预检和封面。当前阶段不解析正文、不下载视频、不抓字幕、不做多帧截图。",
        "",
        "## 时长预检",
        "",
        "| 项 | 结果 |",
        "|---|---|",
        f"| 时长 | {duration_info['duration'] or '未知'} |",
        f"| 状态 | {duration_info['duration_status']} |",
        f"| 成本 | {duration_info['processing_cost_hint']} |",
        f"| 封面 | {metadata['cover_status']} |",
        "",
        "## 封面预览",
        "",
        f"![cover]({metadata['cover']})" if metadata["cover"] else "未获取到可保存封面。",
        "",
        "## 收件标题",
        "",
        clean_hint or "未从转发卡片/输入文本拿到标题。",
        "",
        "## 分级处理",
        "",
        "| 指令 | 行为 |",
        "|---|---|",
        "| `#1` | 只存链接 |",
        "| `#2` | 只存链接并生成 AI chatbox 小卡片 |",
        "| `#3` | Codex 内解析元数据、标题、简介、字幕优先 |",
        "| `#4` | Codex 内深处理结构、要点、选题、行动 |",
        "| `#5` | Codex 内重任务：关键帧/截图/长视频拆段 |",
        "",
    ]
    raw_path.write_text("\n".join(raw_lines), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "slug": slug,
        "article_dir": str(item_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "asset_count": len(assets),
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Store a media URL as a link-only clipping item.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--title", default="", help="Title from the incoming message/card; no platform parsing.")
    parser.add_argument("--out-base", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = capture(args.url, args.task, args.job_id, Path(args.out_base) if args.out_base else None, title_hint=args.title)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}")
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["raw_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
