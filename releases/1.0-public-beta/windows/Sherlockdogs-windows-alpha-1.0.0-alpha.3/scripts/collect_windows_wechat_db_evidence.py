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


def event_epoch(event: dict[str, Any]) -> float:
    for key in ("ts", "created_at", "updated_at"):
        raw = str(event.get(key) or "").strip()
        if not raw:
            continue
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    for key in ("timestamp_end", "timestamp"):
        raw = event.get(key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 10_000_000_000:
            value = value / 1000
        return value
    return 0.0


def event_recent(event: dict[str, Any], since_epoch: float, fallback_path: Path) -> bool:
    epoch = event_epoch(event)
    if epoch:
        return epoch >= since_epoch
    return recent(fallback_path, since_epoch)


def job_level(job: dict[str, Any]) -> int:
    try:
        return int(job.get("task_level") or 0)
    except (TypeError, ValueError):
        pass
    task = str(job.get("task") or "").strip()
    if task == "#":
        return 2
    for level in range(1, 10):
        if task.startswith(f"#{level}"):
            return level
    return 1


def existing_path(value: Any) -> str:
    if not value:
        return ""
    path = Path(str(value))
    return str(path) if path.exists() else ""


def read_config_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "SHERLOCKDOGS_" not in line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        name = left.replace("$env:", "").strip()
        values[name] = right.strip().strip("'\"")
    return values


def completed_codex_card(job: dict[str, Any]) -> bool:
    if job.get("_bucket") != "done" and job.get("status") != "done":
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


def find_windows_jobs(work_dir: Path, since_epoch: float) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for bucket in ["pending", "running", "done", "failed"]:
        for path in iter_json_files(work_dir / "jobs" / bucket):
            if not recent(path, since_epoch):
                continue
            data = read_json(path)
            if data.get("origin") == "windows-wechat-self-chat":
                data["_bucket"] = bucket
                data["_path"] = str(path)
                jobs.append(data)
    return jobs


def find_windows_inbox_events(work_dir: Path, since_epoch: float) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in iter_json_files(work_dir / "jobs" / "inbox-events"):
        if not recent(path, since_epoch):
            continue
        data = read_json(path)
        if str(data.get("event_id", "")).startswith("wechat-windows-") or data.get("origin") == "windows-wechat-self-chat":
            data["_path"] = str(path)
            events.append(data)
    return events


def truth(value: bool) -> str:
    return "ok" if value else "missing"


def has_token(data: Any, token: str) -> bool:
    if not token:
        return True
    try:
        haystack = json.dumps(data, ensure_ascii=False)
    except Exception:
        haystack = str(data)
    return token in haystack


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Windows WeChat DB smoke evidence report.")
    parser.add_argument("--project-dir", default=os.environ.get("SHERLOCKDOGS_PROJECT_DIR", "."))
    parser.add_argument("--lookback-minutes", type=int, default=120)
    parser.add_argument("--require-token", default="", help="Only pass when recent Windows evidence contains this smoke token.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--out-dir", default="")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    since_epoch = time.time() - args.lookback_minutes * 60
    config_path = Path.home() / ".sherlockdogs" / "config.ps1"
    config_values = read_config_values(config_path)
    db_root = os.environ.get("SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR", "")
    if not db_root:
        db_root = config_values.get("SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR", "")
    work_raw = os.environ.get("SHERLOCKDOGS_WORK_DIR") or config_values.get("SHERLOCKDOGS_WORK_DIR", "")
    if not work_raw:
        clipping_raw = os.environ.get("SHERLOCKDOGS_CLIPPING_DIR") or config_values.get("SHERLOCKDOGS_CLIPPING_DIR", "")
        work_raw = str(Path(clipping_raw).expanduser() / "_sherlockdogs") if clipping_raw else str(project_dir)
    work_dir = Path(work_raw).expanduser().resolve()

    all_jobs = find_windows_jobs(work_dir, since_epoch)
    all_inbox_events = find_windows_inbox_events(work_dir, since_epoch)
    run_event_path = work_dir / "runs" / "windows-wechat-inbox.events.jsonl"
    all_run_events = [
        event
        for event in iter_event_lines(run_event_path)
        if (event.get("jobs") or event.get("inbox_event")) and event_recent(event, since_epoch, run_event_path)
    ]
    token = args.require_token.strip()
    jobs = [job for job in all_jobs if has_token(job, token)]
    inbox_events = [event for event in all_inbox_events if has_token(event, token)]
    run_events = [event for event in all_run_events if has_token(event, token)]

    codex_jobs = [
        job
        for job in jobs
        if job_level(job) >= 2
    ]
    completed_jobs = [job for job in codex_jobs if completed_codex_card(job)]
    db_has_messages = bool(db_root and Path(db_root).exists())
    connect_ok = db_has_messages and (work_dir / "jobs" / "windows_receiver_chats.txt").exists()
    token_match = bool(not token or jobs or inbox_events or run_events)
    desktop_received = token_match and bool(inbox_events or run_events or jobs)
    self_chat_received = any(job.get("chat_id") or job.get("extra", {}).get("chat_id") for job in jobs) or desktop_received
    codex_job_created = bool(codex_jobs)
    codex_card = bool(completed_jobs)
    windows_wechat_db = connect_ok and desktop_received and codex_card

    lines = [
        "Sherlockdogs Windows WeChat DB smoke",
        f"generated_at={now_iso()}",
        f"project_dir={project_dir}",
        f"work_dir={work_dir}",
        f"lookback_minutes={args.lookback_minutes}",
        f"db_root={db_root or 'missing'}",
        f"require_token={token or 'none'}",
        f"token_match={truth(token_match)}",
        f"windows_wechat_db={truth(windows_wechat_db)}",
        f"connect_wechat={truth(connect_ok)}",
        f"self_chat_received={truth(self_chat_received)}",
        f"desktop_received={truth(desktop_received)}",
        f"codex_job_created={truth(codex_job_created)}",
        f"codex_card={truth(codex_card)}",
        f"windows_jobs={len(jobs)}",
        f"windows_codex_jobs={len(codex_jobs)}",
        f"windows_completed_codex_jobs={len(completed_jobs)}",
        f"windows_inbox_events={len(inbox_events)}",
        f"windows_run_events={len(run_events)}",
        f"windows_jobs_total={len(all_jobs)}",
        f"windows_inbox_events_total={len(all_inbox_events)}",
        f"windows_run_events_total={len(all_run_events)}",
    ]
    if jobs:
        lines.append(f"latest_job={jobs[0].get('_path')}")
        lines.append(f"latest_job_id={jobs[0].get('job_id', '')}")
        lines.append(f"latest_job_task={jobs[0].get('task', '')}")
        receiver_chat = jobs[0].get("extra", {}).get("receiver_chat") or jobs[0].get("extra", {}).get("chat_id") or jobs[0].get("chat_id", "")
        if receiver_chat:
            lines.append(f"receiver_chat={receiver_chat}")
    if completed_jobs:
        completed_job = completed_jobs[0]
        result = completed_job.get("result") if isinstance(completed_job.get("result"), dict) else {}
        capture = result.get("capture") if isinstance(result.get("capture"), dict) else {}
        thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
        lines.append(f"latest_completed_job={completed_job.get('_path')}")
        lines.append(f"article_dir={capture.get('article_dir', '')}")
        lines.append(f"raw_path={capture.get('raw_path', '')}")
        lines.append(f"readme_path={capture.get('readme_path', '')}")
        lines.append(f"thread_id={thread.get('thread_id', '')}")
        lines.append(f"thread_name={thread.get('thread_name', '')}")
        lines.append(f"thread_path={thread.get('thread_path', '')}")
        lines.append(f"prompt_path={thread.get('prompt_path', '')}")
        lines.append(f"thread_completed={thread.get('completed', '')}")
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
