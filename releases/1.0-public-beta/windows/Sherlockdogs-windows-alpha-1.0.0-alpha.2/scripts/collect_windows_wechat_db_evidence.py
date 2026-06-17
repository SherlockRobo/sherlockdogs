#!/usr/bin/env python3
"""Generate Windows WeChat DB smoke evidence from real Sherlockdogs jobs."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def iter_json_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def iter_event_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def recent(path: Path, since_epoch: float) -> bool:
    try:
        return path.stat().st_mtime >= since_epoch
    except OSError:
        return False


def find_windows_jobs(project_dir: Path, since_epoch: float) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for bucket in ["pending", "running", "done", "failed"]:
        for path in iter_json_files(project_dir / "jobs" / bucket):
            if not recent(path, since_epoch):
                continue
            data = read_json(path)
            if data.get("origin") == "windows-wechat-self-chat":
                data["_bucket"] = bucket
                data["_path"] = str(path)
                jobs.append(data)
    return jobs


def find_windows_inbox_events(project_dir: Path, since_epoch: float) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in iter_json_files(project_dir / "jobs" / "inbox-events"):
        if not recent(path, since_epoch):
            continue
        data = read_json(path)
        if str(data.get("event_id", "")).startswith("wechat-windows-") or data.get("origin") == "windows-wechat-self-chat":
            data["_path"] = str(path)
            events.append(data)
    return events


def truth(value: bool) -> str:
    return "ok" if value else "missing"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Windows WeChat DB smoke evidence report.")
    parser.add_argument("--project-dir", default=os.environ.get("SHERLOCKDOGS_PROJECT_DIR", "."))
    parser.add_argument("--lookback-minutes", type=int, default=120)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    since_epoch = time.time() - args.lookback_minutes * 60
    config_path = Path.home() / ".sherlockdogs" / "config.ps1"
    db_root = os.environ.get("SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR", "")
    if not db_root and config_path.exists():
        for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
            marker = "SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR"
            if marker in line and "=" in line:
                db_root = line.split("=", 1)[1].strip().strip("'\"")
                break

    jobs = find_windows_jobs(project_dir, since_epoch)
    inbox_events = find_windows_inbox_events(project_dir, since_epoch)
    run_events = [
        event
        for event in iter_event_lines(project_dir / "runs" / "windows-wechat-inbox.events.jsonl")
        if event.get("jobs") or event.get("inbox_event")
    ]

    codex_jobs = [
        job
        for job in jobs
        if str(job.get("task", "")).strip() in {"#", "#2"} or int(job.get("task_level") or 0) >= 2
    ]
    db_has_messages = bool(db_root and Path(db_root).exists())
    connect_ok = db_has_messages and (project_dir / "jobs" / "windows_receiver_chats.txt").exists()
    desktop_received = bool(inbox_events or run_events or jobs)
    self_chat_received = any(job.get("chat_id") or job.get("extra", {}).get("chat_id") for job in jobs) or desktop_received
    codex_card = bool(codex_jobs)
    windows_wechat_db = connect_ok and desktop_received and codex_card

    lines = [
        "Sherlockdogs Windows WeChat DB smoke",
        f"generated_at={now_iso()}",
        f"project_dir={project_dir}",
        f"lookback_minutes={args.lookback_minutes}",
        f"db_root={db_root or 'missing'}",
        f"windows_wechat_db={truth(windows_wechat_db)}",
        f"connect_wechat={truth(connect_ok)}",
        f"self_chat_received={truth(self_chat_received)}",
        f"desktop_received={truth(desktop_received)}",
        f"codex_card={truth(codex_card)}",
        f"windows_jobs={len(jobs)}",
        f"windows_codex_jobs={len(codex_jobs)}",
        f"windows_inbox_events={len(inbox_events)}",
        f"windows_run_events={len(run_events)}",
    ]
    if jobs:
        lines.append(f"latest_job={jobs[0].get('_path')}")
        lines.append(f"latest_job_id={jobs[0].get('job_id', '')}")
        lines.append(f"latest_job_task={jobs[0].get('task', '')}")
    if inbox_events:
        lines.append(f"latest_inbox_event={inbox_events[0].get('_path')}")

    report = "\n".join(lines) + "\n"
    print(report, end="")

    if args.write:
        out_dir = Path(args.out_dir) if args.out_dir else project_dir / "dist" / "evidence" / "windows-wechat-db-smoke"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-windows-wechat-db-smoke.txt"
        out_path.write_text(report, encoding="utf-8")
        print(f"report_path={out_path}")

    return 0 if windows_wechat_db else 1


if __name__ == "__main__":
    raise SystemExit(main())
