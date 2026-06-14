#!/usr/bin/env python3
"""Collect public-beta evidence for the phone -> desktop -> Codex path."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DONE_DIR = PROJECT_DIR / "jobs" / "done"
DIST_EVIDENCE_DIR = PROJECT_DIR / "dist" / "evidence" / "mobile-entry-smoke"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def job_level(job: dict[str, Any]) -> int:
    task = str(job.get("task") or "")
    for level in range(1, 10):
        if f"#{level}" in task:
            return level
    return 1


def existing_path(value: Any) -> str:
    if not value:
        return ""
    path = Path(str(value))
    return str(path) if path.exists() else ""


def is_valid_mobile_entry(job: dict[str, Any]) -> bool:
    if job.get("source") != "wechat_inbox":
        return False
    if job.get("origin") != "personal-wechat-self-chat":
        return False
    if job.get("status") != "done":
        return False
    if job_level(job) < 2:
        return False
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    capture = result.get("capture") if isinstance(result.get("capture"), dict) else {}
    thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
    if not result.get("ok") or not capture.get("ok") or not thread.get("ok"):
        return False
    if not thread.get("completed"):
        return False
    if not existing_path(capture.get("article_dir")):
        return False
    if not existing_path(capture.get("raw_path")):
        return False
    if not existing_path(capture.get("readme_path")):
        return False
    if not existing_path(thread.get("prompt_path")):
        return False
    return True


def sorted_done_jobs() -> list[Path]:
    return sorted(DONE_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)


def find_latest_valid_job() -> tuple[Path, dict[str, Any]] | None:
    for path in reversed(sorted_done_jobs()):
        job = load_json(path)
        if job and is_valid_mobile_entry(job):
            return path, job
    return None


def render_report(job_path: Path, job: dict[str, Any]) -> str:
    result = job["result"]
    capture = result["capture"]
    thread = result["thread"]
    metadata = capture.get("metadata") if isinstance(capture.get("metadata"), dict) else {}
    payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
    source_assets = payload.get("source_assets") if isinstance(payload.get("source_assets"), list) else []
    asset_sources = [
        str(item.get("source") or item.get("path") or "")
        for item in source_assets
        if isinstance(item, dict)
    ]
    title = str(metadata.get("title") or job.get("title") or job.get("job_id") or "")
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Sherlockdogs Mobile Entry Smoke Evidence",
        "",
        f"generated_at={generated_at}",
        "mobile_entry=ok",
        "desktop_received=ok",
        "codex_card=ok",
        "",
        f"job_id={job.get('job_id')}",
        f"job_path={job_path}",
        f"source={job.get('source')}",
        f"origin={job.get('origin')}",
        f"task={job.get('task')}",
        f"task_level={job_level(job)}",
        f"title={title}",
        "",
        f"article_dir={capture.get('article_dir')}",
        f"raw_path={capture.get('raw_path')}",
        f"readme_path={capture.get('readme_path')}",
        f"asset_count={capture.get('asset_count')}",
        "",
        f"thread_id={thread.get('thread_id')}",
        f"thread_name={thread.get('thread_name')}",
        f"thread_path={thread.get('thread_path')}",
        f"prompt_path={thread.get('prompt_path')}",
        f"thread_completed={thread.get('completed')}",
    ]
    if asset_sources:
        lines.append("")
        lines.append("source_assets=")
        lines.extend(f"- {source}" for source in asset_sources if source)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate mobile entry smoke evidence from real WeChat jobs.")
    parser.add_argument("--output-dir", default=str(DIST_EVIDENCE_DIR))
    parser.add_argument("--write", action="store_true", help="Write the evidence report.")
    args = parser.parse_args()

    match = find_latest_valid_job()
    if not match:
        print("mobile_entry_verified=false")
        print("mobile_entry_evidence=missing")
        print("reason=no_done_wechat_self_chat_job_with_task_2_or_higher_and_codex_card")
        return 1

    job_path, job = match
    report = render_report(job_path, job)
    if args.write:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_id = str(job.get("job_id") or "mobile-entry").replace("/", "-")
        out_path = out_dir / f"{safe_id}.txt"
        out_path.write_text(report, encoding="utf-8")
        print(f"mobile_entry_verified=true")
        print(f"mobile_entry_evidence={out_path}")
        return 0

    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
