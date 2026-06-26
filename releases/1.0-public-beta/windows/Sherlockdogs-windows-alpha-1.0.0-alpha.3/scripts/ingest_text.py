#!/usr/bin/env python3
"""Extract supported URLs and Sherlockdogs task levels from text, then create jobs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from create_job import PENDING_DIR, build_job, classify_url, safe_id_part


URL_RE = re.compile(r"https?://[^\s<>'\"）)]+")
TASK_RE = re.compile(r"(?im)^\s*(#(?:[1-5]\b.*|ob\b.*|))\s*$")
INLINE_TASK_RE = re.compile(r"(?is)(?:^|\s)(#(?:[1-5]\b[^\r\n#]*|ob\b[^\r\n#]*|))\s*$")
SUPPORTED_SOURCES = {"wechat", "x", "xhs", "bilibili", "youtube", "tiktok", "douyin"}


def clean_url(url: str) -> str:
    return url.rstrip(".,，。;；!！?？)")


def extract_explicit_task(text: str) -> str:
    matches = TASK_RE.findall(text or "")
    if matches:
        return matches[-1].strip()
    match = INLINE_TASK_RE.search(text or "")
    if match:
        return match.group(1).strip()
    return ""


def extract_task(text: str) -> str:
    explicit = extract_explicit_task(text)
    if explicit:
        return explicit
    return "#1"


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in URL_RE.findall(text or ""):
        url = clean_url(match)
        if classify_url(url) in SUPPORTED_SOURCES and url not in urls:
            urls.append(url)
    return urls


def extract_title_hint(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or TASK_RE.match(line):
            continue
        if URL_RE.search(line):
            line = URL_RE.sub("", line).strip(" -_|｜")
        line = re.sub(r"\s+:\S+.*$", "", line).strip()
        line = re.sub(r"^\d+(?:\.\d+)?\s*复制打开抖音，看看", "", line).strip()
        line = line.strip(" #")
        if line:
            return line[:120]
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Codex jobs from pasted clipping text.")
    parser.add_argument("--text", default="", help="Text containing a supported URL and optional # task")
    parser.add_argument("--file", default="", help="Read text from file")
    parser.add_argument("--origin", default="text-ingest")
    parser.add_argument("--pending-dir", default=str(PENDING_DIR))
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    task = extract_task(text)
    title_hint = extract_title_hint(text)
    urls = extract_urls(text)
    pending_dir = Path(args.pending_dir)
    pending_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for url in urls:
        job = build_job(url, task, args.origin, extra={"title": title_hint} if title_hint else None)
        path = pending_dir / f"{safe_id_part(job['job_id'], 64)}.json"
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        jobs.append({"job_id": job["job_id"], "url": url, "task": task, "path": str(path)})

    print(json.dumps({"ok": True, "count": len(jobs), "jobs": jobs}, ensure_ascii=False, indent=2))
    return 0 if jobs else 1


if __name__ == "__main__":
    raise SystemExit(main())
