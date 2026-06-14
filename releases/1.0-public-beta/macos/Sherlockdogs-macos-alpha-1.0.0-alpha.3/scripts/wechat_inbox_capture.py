#!/usr/bin/env python3
"""Store non-link personal WeChat inbox messages as clipping items."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR  # noqa: E402

BASE_DIR = CLIPPING_DIR / "wechat-inbox"
URL_RE = re.compile(r"https?://\S+")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slug_part(text: str, limit: int = 54) -> str:
    text = clean_text(text)
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-").lower()
    return (text or "wechat-inbox")[:limit].strip("-")


def digest_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:10]


def file_ext(path: Path) -> str:
    try:
        head = path.read_bytes()[:16]
    except Exception:
        head = b""
    if head.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if head.startswith(b"\x89PNG"):
        return ".png"
    if head.startswith(b"RIFF") and b"WEBP" in head:
        return ".webp"
    guessed = mimetypes.guess_extension(mimetypes.guess_type(str(path))[0] or "")
    return guessed if guessed in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def copy_image(source_path: str, assets_dir: Path, stem: str) -> dict[str, Any]:
    if not source_path:
        return {"ok": False, "status": "missing-source-path"}
    src = Path(source_path)
    if not src.exists():
        return {"ok": False, "status": "source-not-found", "source": source_path}
    assets_dir.mkdir(parents=True, exist_ok=True)
    ext = ".jpg" if file_ext(src) == ".jpeg" else file_ext(src)
    filename = f"{slug_part(stem, 36) or 'wechat-image'}-{digest_text(source_path)}{ext}"
    dest = assets_dir / filename
    shutil.copyfile(src, dest)
    return {
        "ok": True,
        "status": "ok",
        "local": f"assets/{filename}",
        "source": source_path,
        "bytes": dest.stat().st_size,
    }


def title_from_payload(payload: dict[str, Any], fallback: str) -> str:
    text = clean_text(str(payload.get("text") or ""))
    if text:
        title = clean_text(URL_RE.sub("", text).strip(" -_|｜"))
        if title:
            return title[:80]
    urls = payload.get("urls") if isinstance(payload.get("urls"), list) else []
    if urls:
        return clean_text(str(urls[0]))[:80]
    if payload.get("kind") == "image":
        return fallback or "微信图片剪藏"
    if payload.get("kind") == "bundle":
        return fallback or "微信剪藏包"
    return fallback or "微信剪藏"


def payload_images(payload: dict[str, Any]) -> list[dict[str, Any]]:
    images = payload.get("images")
    if isinstance(images, list):
        return [image for image in images if isinstance(image, dict)]
    image = payload.get("image")
    if isinstance(image, dict) and image:
        return [image]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a personal WeChat non-link message.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--job-file", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    job = json.loads(Path(args.job_file).read_text(encoding="utf-8"))
    extra = job.get("extra") if isinstance(job.get("extra"), dict) else {}
    payload = extra.get("payload") if isinstance(extra.get("payload"), dict) else {}
    title = title_from_payload(payload, str(extra.get("title") or ""))
    stamp = datetime.fromtimestamp(int(payload.get("timestamp") or datetime.now().timestamp())).strftime("%Y%m%d")
    article_dir = BASE_DIR / f"{stamp}-{slug_part(title)}-{digest_text(args.url)}"
    assets_dir = article_dir / "assets"
    article_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, Any]] = []
    for idx, image in enumerate(payload_images(payload), start=1):
        asset = copy_image(str(image.get("source_path") or ""), assets_dir, f"{title}-{idx}")
        if asset.get("ok"):
            assets.append(asset)

    description = clean_text(str(payload.get("text") or ""))
    urls = payload.get("urls") if isinstance(payload.get("urls"), list) else []
    if not description and urls:
        description = clean_text(str(urls[0]))
    if not description and payload_images(payload):
        description = "图片剪藏，已保存本地预览。" if assets else "图片剪藏，暂未定位到本地原图。"

    raw_path = article_dir / "raw.md"
    metadata_path = article_dir / "metadata.json"
    raw_lines = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        'source: "wechat-inbox"',
        f"url: {json.dumps(args.url, ensure_ascii=False)}",
        f"created: {json.dumps(now_iso(), ensure_ascii=False)}",
        f"task: {json.dumps(args.task, ensure_ascii=False)}",
        "---",
        "",
        f"# {title}",
        "",
    ]
    if urls:
        raw_lines.extend(["## 链接", ""])
        raw_lines.extend(f"- {url}" for url in urls)
        raw_lines.append("")
    if payload.get("text"):
        raw_lines.extend(["## 文字", "", str(payload["text"]).strip(), ""])
    if assets:
        raw_lines.extend(["## 图片", ""])
        raw_lines.extend("![](" + asset["local"] + ")" for asset in assets)
        raw_lines.append("")
    if payload_images(payload) and not assets:
        raw_lines.extend(["```xml", str(payload.get("raw_preview") or ""), "```", ""])
    raw_path.write_text("\n".join(raw_lines), encoding="utf-8")

    metadata = {
        "title": title,
        "account": "个人微信自聊",
        "source": "wechat-inbox",
        "url": args.url,
        "urls": urls,
        "primary_url": str(payload.get("primary_url") or (urls[0] if urls else "")),
        "description": description,
        "duration": "",
        "processing_cost_hint": "低：本地文本/图片",
        "assets": assets,
        "payload": payload,
        "created_at": now_iso(),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "ok": True,
        "source": "wechat_inbox",
        "article_dir": str(article_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "asset_count": len(assets),
        "metadata": metadata,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(raw_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
