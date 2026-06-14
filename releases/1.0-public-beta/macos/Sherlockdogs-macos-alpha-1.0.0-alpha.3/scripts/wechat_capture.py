#!/usr/bin/env python3
"""Capture a public WeChat article as local Markdown and assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import CLIPPING_DIR  # noqa: E402

INBOX_DIR = CLIPPING_DIR / "wechat"
DEFAULT_TIMEOUT = 30


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slug_part(text: str, limit: int = 54) -> str:
    text = clean_text(text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-").lower()
    return (text or "wechat-article")[:limit].strip("-")


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


def fetch_html(url: str, attempts: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=request_headers(), timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or response.encoding
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.5 * (attempt + 1))
    raise last_error or RuntimeError("fetch_html failed")


def meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(str(tag.get("content")))
    return ""


def selected_text(soup: BeautifulSoup, selector: str) -> str:
    tag = soup.select_one(selector)
    return clean_text(tag.get_text(" ", strip=True)) if tag else ""


def script_value(html: str, pattern: str) -> str:
    match = re.search(pattern, html)
    return clean_text(match.group(1)) if match else ""


def meaningful_title(title: str) -> bool:
    return bool(title and title not in {"untitled", "微信公众平台"})


def extract_metadata(url: str, html: str, soup: BeautifulSoup, hints: dict[str, str] | None = None) -> dict[str, Any]:
    hints = hints or {}
    title = selected_text(soup, "#activity-name") or clean_text(soup.title.get_text(" ", strip=True) if soup.title else "")
    title = title or meta_content(soup, "og:title", "twitter:title") or "untitled"
    if not meaningful_title(title) and hints.get("title"):
        title = hints["title"]
    account = selected_text(soup, "#js_name")
    author = selected_text(soup, "#meta_content .rich_media_meta_text")
    description = meta_content(soup, "og:description", "description")
    cover = meta_content(soup, "og:image", "twitter:image")
    if not account and hints.get("account"):
        account = hints["account"]
    if not description and hints.get("description"):
        description = hints["description"]
    if not cover and hints.get("cover"):
        cover = hints["cover"]
    published_at = (
        script_value(html, r'var\s+ct\s*=\s*"([^"]+)"')
        or script_value(html, r'publish_time\s*=\s*"([^"]+)"')
        or meta_content(soup, "article:published_time")
    )
    source_id = script_value(html, r'var\s+msgid\s*=\s*"([^"]+)"') or url_hash(url)
    return {
        "source": "wechat",
        "source_id": source_id,
        "url": url,
        "title": title,
        "account": account,
        "author": author,
        "description": description,
        "cover": cover,
        "published_at": published_at,
        "captured_at": now_iso(),
    }


def is_limited_or_verify_page(html: str, soup: BeautifulSoup) -> bool:
    if "mmbizwap:secitptpage/verify" in html or "verify.html" in html:
        return True
    return not (soup.select_one("#js_content") or soup.select_one(".rich_media_content"))


def fallback_content(metadata: dict[str, Any], url: str) -> BeautifulSoup:
    parts = ["<article>"]
    description = clean_text(str(metadata.get("description") or ""))
    if description:
        parts.append(f"<p>{description}</p>")
    cover = str(metadata.get("cover") or "").strip()
    if cover:
        parts.append(f'<p><img src="{cover}" alt="{metadata.get("title") or "cover"}"></p>')
    parts.append(f'<p><a href="{url}">原文链接</a></p>')
    parts.append("</article>")
    return BeautifulSoup("\n".join(parts), "html.parser")


def extension_for(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip())
    if guessed in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        return ".jpg" if guessed == ".jpeg" else guessed
    return ".jpg"


def download_image(url: str, assets_dir: Path, stem: str, index: int, attempts: int = 2) -> str:
    assets_dir.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=request_headers(), timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1.2 * (attempt + 1))
    else:
        raise last_error or RuntimeError("download_image failed")
    ext = extension_for(url, response.headers.get("content-type"))
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    filename = f"{slug_part(stem, 38)}-{index:02d}-{digest}{ext}"
    path = assets_dir / filename
    path.write_bytes(response.content)
    return f"assets/{filename}"


def normalize_content(
    content: BeautifulSoup,
    base_url: str,
    assets_dir: Path,
    title: str,
    initial_seen: set[str] | None = None,
) -> list[dict[str, str]]:
    assets: list[dict[str, str]] = []
    seen: set[str] = set(initial_seen or set())

    for tag in content.find_all(["script", "style", "iframe"]):
        tag.decompose()

    for idx, img in enumerate(content.find_all("img"), start=1):
        src = img.get("data-src") or img.get("data-backsrc") or img.get("src")
        if not src:
            continue
        src = urljoin(base_url, str(src))
        if src in seen:
            img.decompose()
            continue
        seen.add(src)
        try:
            local = download_image(src, assets_dir, title, idx)
            img["src"] = local
            img["alt"] = clean_text(img.get("alt") or title)
            assets.append({"source": src, "local": local, "kind": "image"})
        except Exception as exc:
            img["alt"] = f"image download failed: {src}"
            assets.append({"source": src, "local": "", "kind": f"download-failed: {exc}"})

    for tag in content.find_all(True):
        # Keep semantic structure; strip noisy inline styling after image extraction.
        for attr in ("style", "class", "id", "data-tools", "data-id"):
            tag.attrs.pop(attr, None)

    return assets


def markdown_frontmatter(metadata: dict[str, Any], task: str, assets: list[dict[str, str]]) -> str:
    def js(value: Any) -> str:
        return json.dumps("" if value is None else str(value), ensure_ascii=False)

    lines = [
        "---",
        "source: wechat",
        "type: article_raw",
        f"source_id: {js(metadata.get('source_id'))}",
        f"url: {js(metadata.get('url'))}",
        f"title: {js(metadata.get('title'))}",
        f"account: {js(metadata.get('account'))}",
        f"author: {js(metadata.get('author'))}",
        f"published_at: {js(metadata.get('published_at'))}",
        f"captured_at: {js(metadata.get('captured_at'))}",
        f"task: {js(task)}",
        f"asset_count: {len([a for a in assets if a.get('local')])}",
        "status: raw",
        "tags:",
        "  - wechat-inbox",
        "---",
        "",
    ]
    return "\n".join(lines)


def capture(url: str, task: str, job_id: str, out_base: Path, hints: dict[str, str] | None = None) -> dict[str, Any]:
    hints = hints or {}
    fetch_error = ""
    try:
        html = fetch_html(url)
    except Exception as exc:
        if not any(clean_text(str(hints.get(key) or "")) for key in ("title", "description", "account", "cover")):
            raise
        html = ""
        fetch_error = str(exc)

    soup = BeautifulSoup(html or "<html><body></body></html>", "html.parser")
    metadata = extract_metadata(url, html, soup, hints=hints)
    limited_page = bool(fetch_error) or is_limited_or_verify_page(html, soup)
    if fetch_error:
        metadata["fetch_status"] = "fetch_failed_card_fallback"
        metadata["fetch_error"] = fetch_error[:500]
    elif limited_page:
        metadata["fetch_status"] = "limited_or_verify_page"
    slug = f"{datetime.now().strftime('%Y%m%d')}-{slug_part(metadata['title'])}-{url_hash(url)}"
    article_dir = out_base / slug
    assets_dir = article_dir / "assets"
    article_dir.mkdir(parents=True, exist_ok=True)

    content = fallback_content(metadata, url).article if limited_page else (
        soup.select_one("#js_content")
        or soup.select_one(".rich_media_content")
        or soup.select_one("article")
        or soup.select_one("main")
        or soup.body
    )
    if content is None:
        raise RuntimeError("Could not locate article content")

    assets: list[dict[str, str]] = []
    seen_sources: set[str] = set()
    cover = str(metadata.get("cover") or "").strip()
    if cover:
        try:
            local = download_image(cover, assets_dir, metadata["title"], 0)
            assets.append({"source": cover, "local": local, "kind": "cover"})
            seen_sources.add(cover)
            metadata["cover_local"] = local
        except Exception as exc:
            assets.append({"source": cover, "local": "", "kind": f"cover-download-failed: {exc}"})

    assets.extend(normalize_content(content, url, assets_dir, metadata["title"], initial_seen=seen_sources))
    body_md = html_to_markdown(str(content), heading_style="ATX", bullets="-")
    body_md = re.sub(r"\n{3,}", "\n\n", body_md).strip()

    raw_md = (
        markdown_frontmatter(metadata, task, assets)
        + f"# {metadata['title']}\n\n"
        + f"[原文链接]({url})\n\n"
        + body_md
        + "\n"
    )

    raw_path = article_dir / "raw.md"
    html_path = article_dir / "article.html"
    metadata_path = article_dir / "metadata.json"
    raw_path.write_text(raw_md, encoding="utf-8")
    html_path.write_text(html or str(content), encoding="utf-8")
    metadata.update({"job_id": job_id, "slug": slug, "article_dir": str(article_dir), "raw_path": str(raw_path)})
    metadata["assets"] = assets
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "slug": slug,
        "article_dir": str(article_dir),
        "raw_path": str(raw_path),
        "metadata_path": str(metadata_path),
        "asset_count": len([a for a in assets if a.get("local")]),
        "metadata": metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a public WeChat article to Obsidian raw Markdown.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--task", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--out-base", default=str(INBOX_DIR))
    parser.add_argument("--title", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--account", default="")
    parser.add_argument("--cover", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        hints = {
            "title": clean_text(args.title),
            "description": clean_text(args.description),
            "account": clean_text(args.account),
            "cover": clean_text(args.cover),
        }
        result = capture(args.url, args.task, args.job_id, Path(args.out_base), hints=hints)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result["raw_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
