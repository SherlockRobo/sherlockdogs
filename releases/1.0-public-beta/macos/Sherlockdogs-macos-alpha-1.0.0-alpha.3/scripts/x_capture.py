#!/usr/bin/env python3
"""Capture an X/Twitter URL as local Markdown and metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR  # noqa: E402

INBOX_DIR = CLIPPING_DIR / "x"
DEFAULT_TIMEOUT = 25


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_display_text(text: str) -> str:
    text = re.sub(r"\bpic\.twitter\.com/\S+", "", text or "")
    text = re.sub(r"https?://\S+", "", text)
    return clean_text(text).strip("\"'“”‘’ ")


def ellipsize(text: str, limit: int = 78) -> str:
    text = clean_display_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def slug_part(text: str, limit: int = 54) -> str:
    text = clean_text(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-").lower()
    return (text or "x-post")[:limit].strip("-")


def url_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def request_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.endswith("twitter.com"):
        host = host.replace("twitter.com", "x.com")
    return parsed._replace(netloc=host).geturl()


def fetch_html(url: str) -> tuple[str, str]:
    response = requests.get(url, headers=request_headers(), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return response.text, response.url


def fetch_oembed(url: str) -> dict[str, Any]:
    endpoint = "https://publish.x.com/oembed?url=" + quote(url, safe="")
    response = requests.get(endpoint, headers=request_headers(), timeout=DEFAULT_TIMEOUT)
    if response.status_code == 404:
        return {}
    response.raise_for_status()
    payload = response.json()
    return payload if isinstance(payload, dict) else {}


def meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(str(tag.get("content")))
    return ""


def extension_for(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip())
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if guessed == ".jpeg" else guessed
    return ".jpg"


def download_image(url: str, assets_dir: Path, stem: str, index: int) -> str:
    assets_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, headers=request_headers(), timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()
    ext = extension_for(url, response.headers.get("content-type"))
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    filename = f"{slug_part(stem, 38)}-{index:02d}-{digest}{ext}"
    path = assets_dir / filename
    path.write_bytes(response.content)
    return f"assets/{filename}"


def fallback_title(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 3 and parts[-2] == "status":
        return f"X post @{parts[0]} {parts[-1]}"
    return f"X clip {url_hash(url)}"


def parse_status_parts(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 3 and parts[-2] == "status":
        return parts[0], parts[-1]
    return "", ""


def tweet_text_from_oembed(payload: dict[str, Any]) -> str:
    html = str(payload.get("html") or "")
    soup = BeautifulSoup(html, "html.parser")
    paragraph = soup.find("p")
    return clean_text(paragraph.get_text(" ", strip=True)) if paragraph else ""


def published_at_from_oembed(payload: dict[str, Any]) -> str:
    html = str(payload.get("html") or "")
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    return clean_text(links[-1].get_text(" ", strip=True)) if links else ""


def title_from_text(author: str, handle: str, text: str, url: str) -> str:
    if text:
        prefix = author or (f"@{handle}" if handle else "X")
        return f"X｜{prefix}: {ellipsize(text)}"
    return fallback_title(url)


def empty_content_reason(fetch_error: str) -> str:
    reason = clean_text(fetch_error)
    if not reason:
        return "X 公开页面和嵌入接口未返回正文"
    if "403" in reason:
        return "X 公开页面或嵌入接口返回 403，后台无登录态时不可读"
    if "404" in reason:
        return "X 返回 404，链接可能不存在或不可公开访问"
    return f"X 公开抓取受限：{reason[:160]}"


def extract_metadata(url: str, html: str, final_url: str, fetch_error: str = "") -> dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")
    handle, tweet_id = parse_status_parts(url)
    oembed: dict[str, Any] = {}
    try:
        oembed = fetch_oembed(url)
    except Exception as exc:
        if fetch_error:
            fetch_error = f"{fetch_error}; oEmbed: {exc}"
        else:
            fetch_error = f"oEmbed: {exc}"
    oembed_text = tweet_text_from_oembed(oembed) if oembed else ""
    oembed_author = clean_text(str(oembed.get("author_name") or "")) if oembed else ""
    oembed_url = clean_text(str(oembed.get("url") or "")) if oembed else ""
    title = meta_content(soup, "og:title", "twitter:title")
    description = meta_content(soup, "og:description", "twitter:description", "description")
    image = meta_content(soup, "og:image", "twitter:image")
    author = oembed_author
    title_match = re.match(r"(.+?)\s+on\s+X:", title)
    if title_match and not author:
        author = clean_text(title_match.group(1))
    if oembed_text:
        description = oembed_text
        title = title_from_text(author, handle, oembed_text, url)
    if not title:
        title = fallback_title(url)
    capture_status = "ok" if (description or image) else "empty-public-content"
    capture_note = ""
    if capture_status == "empty-public-content":
        capture_note = empty_content_reason(fetch_error)
        description = (
            f"未抓到正文：{capture_note}。"
            "可能是测试占位链接、帖子已删除/不可公开访问，或需要浏览器登录态。"
        )
        title = f"X待补｜@{handle} {tweet_id}" if handle and tweet_id else title
    return {
        "source": "x",
        "source_id": tweet_id or url_hash(url),
        "url": url,
        "canonical_url": normalize_url(oembed_url or final_url or url),
        "title": title,
        "account": author or (f"@{handle}" if handle else ""),
        "author": author,
        "description": description,
        "cover": image,
        "published_at": published_at_from_oembed(oembed) if oembed else "",
        "captured_at": now_iso(),
        "fetch_error": fetch_error,
        "capture_status": capture_status,
        "capture_note": capture_note,
        "tweet_id": tweet_id,
        "handle": handle,
        "capture_method": "oembed+html" if oembed_text else "html-fallback",
    }


def markdown_frontmatter(metadata: dict[str, Any], task: str, assets: list[dict[str, str]]) -> str:
    def js(value: Any) -> str:
        return json.dumps("" if value is None else str(value), ensure_ascii=False)

    lines = [
        "---",
        "source: x",
        "type: social_post_raw",
        f"source_id: {js(metadata.get('source_id'))}",
        f"url: {js(metadata.get('url'))}",
        f"canonical_url: {js(metadata.get('canonical_url'))}",
        f"title: {js(metadata.get('title'))}",
        f"account: {js(metadata.get('account'))}",
        f"author: {js(metadata.get('author'))}",
        f"published_at: {js(metadata.get('published_at'))}",
        f"captured_at: {js(metadata.get('captured_at'))}",
        f"task: {js(task)}",
        f"asset_count: {len([a for a in assets if a.get('local')])}",
        "status: raw",
        "tags:",
        "  - x-inbox",
        "---",
        "",
    ]
    return "\n".join(lines)


def capture(url: str, task: str, job_id: str, out_base: Path) -> dict[str, Any]:
    source_url = normalize_url(url)
    html = ""
    final_url = source_url
    fetch_error = ""
    try:
        html, final_url = fetch_html(source_url)
    except Exception as exc:
        fetch_error = str(exc)

    metadata = extract_metadata(source_url, html, final_url, fetch_error=fetch_error)
    slug = f"{datetime.now().strftime('%Y%m%d')}-{slug_part(metadata['title'])}-{url_hash(source_url)}"
    item_dir = out_base / slug
    assets_dir = item_dir / "assets"
    item_dir.mkdir(parents=True, exist_ok=True)

    assets: list[dict[str, str]] = []
    cover = str(metadata.get("cover") or "")
    if cover:
        try:
            local = download_image(cover, assets_dir, metadata["title"], 1)
            assets.append({"source": cover, "local": local, "kind": "image"})
        except Exception as exc:
            assets.append({"source": cover, "local": "", "kind": f"download-failed: {exc}"})

    description = str(metadata.get("description") or "").strip()
    topic = ellipsize(description, 140) if description else "公开页面未返回正文，主题需后续用登录态或手动补充。"
    if metadata.get("capture_status") == "empty-public-content":
        topic = str(metadata.get("capture_note") or topic)
    body_lines = [
        markdown_frontmatter(metadata, task, assets),
        f"# {metadata['title']}",
        "",
        f"[原文链接]({source_url})",
        "",
        "## 主题",
        "",
        topic,
        "",
        "## 内容",
        "",
        description or "公开页面未返回正文。已保存链接，后续可用浏览器、登录态或手动补充方式继续处理。",
        "",
    ]
    if fetch_error:
        body_lines.extend(["## 抓取状态", "", f"公开抓取受限：`{fetch_error}`", ""])
    if assets:
        body_lines.extend(["## 图片", ""])
        for asset in assets:
            if asset.get("local"):
                body_lines.append(f"![image]({asset['local']})")
        body_lines.append("")

    raw_path = item_dir / "raw.md"
    html_path = item_dir / "page.html"
    metadata_path = item_dir / "metadata.json"
    raw_path.write_text("\n".join(body_lines), encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    metadata.update({"job_id": job_id, "slug": slug, "article_dir": str(item_dir), "raw_path": str(raw_path)})
    metadata["assets"] = assets
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "slug": slug,
        "article_dir": str(item_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "asset_count": len([a for a in assets if a.get("local")]),
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture an X/Twitter URL to Obsidian raw Markdown.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--out-base", default=str(INBOX_DIR))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        result = capture(args.url, args.task, args.job_id, Path(args.out_base))
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
