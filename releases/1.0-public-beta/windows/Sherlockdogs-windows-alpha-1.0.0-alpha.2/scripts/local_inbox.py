#!/usr/bin/env python3
"""Watch a local Sherlockdogs Inbox folder and create clipping jobs.

The local Inbox is the cross-platform entry point: any sync tool can write
files into it, while Sherlockdogs only sees ordinary local files.
"""

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

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from create_job import PENDING_DIR, build_job, classify_url, now_iso as job_now_iso, parse_task, safe_id_part  # noqa: E402
from ingest_text import extract_explicit_task, extract_task, extract_title_hint  # noqa: E402
from sdogs_paths import INBOX_DIR as DEFAULT_INBOX_DIR, JOBS_DIR, PROJECT_DIR, RUNS_DIR  # noqa: E402
STATE_FILE = JOBS_DIR / "local_inbox_state.json"
EVENT_LOG = RUNS_DIR / "local-inbox.events.jsonl"
SUPPORTED_SOURCES = {"wechat", "x", "xhs", "bilibili", "youtube", "tiktok", "douyin"}
TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".url", ".webloc"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
DOCUMENT_SUFFIXES = {".pdf"}
IGNORED_NAMES = {".ds_store", "thumbs.db"}
URL_RE = re.compile(r"https?://[^\s<>'\"）)]+")
URL_FILE_RE = re.compile(r"(?im)^\s*URL\s*=\s*(https?://\S+)\s*$")
WEBLOC_RE = re.compile(r"<string>(https?://.*?)</string>", re.DOTALL | re.IGNORECASE)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_event(event: dict[str, Any]) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    event.setdefault("ts", now_iso())
    with EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def clean_url(url: str) -> str:
    return url.rstrip(".,，。;；!！?？)]}」』”")


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in URL_FILE_RE.findall(text or ""):
        url = clean_url(match)
        if url and url not in urls:
            urls.append(url)
    for match in WEBLOC_RE.findall(text or ""):
        url = clean_url(match.strip())
        if url and url not in urls:
            urls.append(url)
    for match in URL_RE.findall(text or ""):
        url = clean_url(match)
        if url and url not in urls:
            urls.append(url)
    return urls


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def path_kind(path: Path) -> str:
    if path.is_dir():
        return "bundle"
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return "text"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix in DOCUMENT_SUFFIXES:
        return "document"
    return "file"


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def iter_bundle_files(path: Path) -> list[Path]:
    files = []
    for item in sorted(path.rglob("*")):
        if item.name.startswith(".") or item.name.lower() in IGNORED_NAMES:
            continue
        if item.is_file():
            files.append(item)
    return files


def entry_mtime_ns(path: Path) -> int:
    if path.is_dir():
        mtimes = [path.stat().st_mtime_ns]
        for item in iter_bundle_files(path):
            try:
                mtimes.append(item.stat().st_mtime_ns)
            except OSError:
                pass
        return max(mtimes)
    return path.stat().st_mtime_ns


def entry_size(path: Path) -> int:
    if path.is_dir():
        total = 0
        for item in iter_bundle_files(path):
            try:
                total += item.stat().st_size
            except OSError:
                pass
        return total
    return path.stat().st_size


def entry_signature(path: Path) -> str:
    payload = {
        "path": str(path.resolve()),
        "kind": "dir" if path.is_dir() else "file",
        "mtime_ns": entry_mtime_ns(path),
        "size": entry_size(path),
    }
    return hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def is_settled(path: Path, settle_seconds: int) -> bool:
    try:
        mtime = entry_mtime_ns(path) / 1_000_000_000
    except OSError:
        return False
    return time.time() - mtime >= settle_seconds


def file_payload(path: Path, root: Path | None = None) -> dict[str, Any]:
    rel = str(path.relative_to(root)) if root and path.is_relative_to(root) else path.name
    mime = mimetypes.guess_type(str(path))[0] or ""
    return {
        "name": path.name,
        "relative_path": rel,
        "path": str(path),
        "kind": path_kind(path),
        "suffix": path.suffix.lower(),
        "mime": mime,
        "size": path.stat().st_size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
    }


def text_from_entry(path: Path) -> str:
    if path.is_file() and path_kind(path) == "text":
        return read_text_file(path)
    if path.is_dir():
        chunks = []
        for item in iter_bundle_files(path):
            if path_kind(item) == "text":
                chunks.append(f"## {item.relative_to(path)}\n\n{read_text_file(item)}")
        return "\n\n".join(chunks).strip()
    return ""


def title_for_entry(path: Path, text: str, files: list[dict[str, Any]]) -> str:
    title = extract_title_hint(text)
    if title:
        return title
    if path.is_dir():
        return path.name
    if path_kind(path) == "image":
        return f"图片剪藏：{path.stem}"
    if path_kind(path) == "video":
        return f"视频剪藏：{path.stem}"
    return path.stem or path.name


def digest_entry(path: Path, text: str) -> str:
    body = "\n".join([str(path.resolve()), str(entry_size(path)), str(entry_mtime_ns(path)), text[:1000]])
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()[:10]


def build_local_job(path: Path, task: str, title: str, text: str, urls: list[str], files: list[dict[str, Any]]) -> dict[str, Any]:
    task_level, normalized_task, original_task = parse_task(task)
    digest = digest_entry(path, text)
    created_at = job_now_iso()
    kind = "bundle" if path.is_dir() else path_kind(path)
    return {
        "version": 1,
        "job_id": f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-local-inbox-{digest}",
        "status": "pending",
        "source": "local_inbox",
        "origin": "local-inbox-folder",
        "url": f"file://{path.resolve()}",
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "created_at": created_at,
        "updated_at": created_at,
        "attempts": 0,
        "extra": {
            "inbox": "local-folder",
            "input_path": str(path.resolve()),
            "title": title,
            "payload": {
                "kind": kind,
                "title": title,
                "text": text,
                "urls": urls,
                "primary_url": urls[0] if urls else "",
                "files": files,
                "captured_from": str(path.resolve()),
            },
        },
    }


def write_job(job: dict[str, Any], dry_run: bool) -> Path:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    path = PENDING_DIR / f"{safe_id_part(job['job_id'], 64)}.json"
    if not dry_run:
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def create_jobs_for_entry(path: Path, dry_run: bool) -> list[dict[str, Any]]:
    text = text_from_entry(path)
    urls = extract_urls(text)
    files = [file_payload(path)] if path.is_file() else [file_payload(item, path) for item in iter_bundle_files(path)]
    task = extract_task(text)
    title = title_for_entry(path, text, files)
    jobs = []

    supported_urls = [url for url in urls if classify_url(url) in SUPPORTED_SOURCES]
    if supported_urls and path_kind(path) == "text":
        for url in supported_urls:
            job = build_job(
                url,
                task,
                "local-inbox-folder",
                extra={
                    "inbox": "local-folder",
                    "input_path": str(path.resolve()),
                    "title": title,
                    "raw_preview": text[:3000],
                },
            )
            job_path = write_job(job, dry_run)
            jobs.append({"job_id": job["job_id"], "source": job["source"], "url": url, "task": job["task"], "path": str(job_path)})
        return jobs

    job = build_local_job(path, task, title, text, urls, files)
    job_path = write_job(job, dry_run)
    jobs.append(
        {
            "job_id": job["job_id"],
            "source": "local_inbox",
            "url": job["url"],
            "task": job["task"],
            "path": str(job_path),
            "kind": job["extra"]["payload"]["kind"],
        }
    )
    return jobs


def scan_entries(inbox_dir: Path) -> list[Path]:
    inbox_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in sorted(inbox_dir.iterdir()):
        if path.name.startswith(".") or path.name.lower() in IGNORED_NAMES:
            continue
        if path.is_file() or path.is_dir():
            entries.append(path)
    return entries


def run_once(inbox_dir: Path, dry_run: bool, settle_seconds: int, limit: int) -> dict[str, Any]:
    state = read_json(STATE_FILE, {})
    processed = set(state.get("processed_signatures") or [])
    results = []
    for entry in scan_entries(inbox_dir):
        if len(results) >= limit:
            break
        if not is_settled(entry, settle_seconds):
            continue
        try:
            signature = entry_signature(entry)
        except OSError:
            continue
        if signature in processed:
            continue
        jobs = create_jobs_for_entry(entry, dry_run=dry_run)
        event = {
            "signature": signature,
            "input_path": str(entry.resolve()),
            "kind": path_kind(entry),
            "jobs": jobs,
        }
        results.append(event)
        if not dry_run:
            processed.add(signature)
            append_event(event)

    if not dry_run:
        state["processed_signatures"] = sorted(processed)[-3000:]
        state["last_seen_at"] = now_iso()
        state["inbox_dir"] = str(inbox_dir)
        write_json(STATE_FILE, state)

    return {"ok": True, "processed": len(results), "inbox_dir": str(inbox_dir), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Sherlockdogs jobs from a local Inbox folder.")
    parser.add_argument("--inbox-dir", default=str(DEFAULT_INBOX_DIR))
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=10.0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--settle-seconds", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    inbox_dir = Path(args.inbox_dir).expanduser()
    while True:
        try:
            print(
                json.dumps(
                    run_once(inbox_dir=inbox_dir, dry_run=args.dry_run, settle_seconds=args.settle_seconds, limit=args.limit),
                    ensure_ascii=False,
                ),
                flush=True,
            )
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc), "ts": now_iso()}, ensure_ascii=False), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
