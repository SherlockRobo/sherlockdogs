#!/usr/bin/env python3
"""Create a pending Sherlockdogs clipping job."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sdogs_paths import JOBS_DIR, PROJECT_DIR  # noqa: E402

PENDING_DIR = JOBS_DIR / "pending"
LEGACY_DEFAULT_TASK = "默认蒸馏：提炼核心结论、关键支撑、可复用观点、写作选题、行动建议。"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def safe_id_part(text: str, limit: int = 14) -> str:
    text = re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-").lower()
    return (text or "wechat")[:limit]


def classify_url(url: str) -> str:
    lowered = url.lower()
    if "mp.weixin.qq.com/" in lowered:
        return "wechat"
    if re.search(r"https?://([^/]+\.)?(xiaohongshu\.com|xhslink\.com)/", lowered):
        return "xhs"
    if re.search(r"https?://([^/]+\.)?(x\.com|twitter\.com)/", lowered):
        return "x"
    if re.search(r"https?://([^/]+\.)?(bilibili\.com|b23\.tv)/", lowered):
        return "bilibili"
    if re.search(r"https?://([^/]+\.)?(youtube\.com|youtu\.be)/", lowered):
        return "youtube"
    if re.search(r"https?://([^/]+\.)?(tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/", lowered):
        return "tiktok"
    if re.search(r"https?://([^/]+\.)?(douyin\.com|v\.douyin\.com|iesdouyin\.com)/", lowered):
        return "douyin"
    return "web"


def make_job_id(url: str, source: str | None = None) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{stamp}-{source or classify_url(url)}-{digest}"


def validate_url(url: str) -> None:
    if not url.startswith(("http://", "https://")):
        raise ValueError("url must start with http:// or https://")


def parse_task(task: str) -> tuple[int, str, str]:
    original = (task or "").strip()
    if not original or original == LEGACY_DEFAULT_TASK:
        return 1, "#1", original
    if original == "#":
        return 2, "#2", original

    level_match = re.match(r"^#([1-5])\b(.*)$", original, flags=re.IGNORECASE)
    if level_match:
        level = int(level_match.group(1))
        tail = level_match.group(2).strip()
        return level, f"#{level}" + (f" {tail}" if tail else ""), original

    if re.match(r"^#ob\b", original, flags=re.IGNORECASE):
        return 4, original, original

    if original.startswith("#"):
        return 2, original, original

    return 1, "#1", original


def build_job(url: str, task: str, origin: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    validate_url(url)
    task_level, normalized_task, original_task = parse_task(task)
    source = classify_url(url)
    return {
        "version": 1,
        "job_id": make_job_id(url, source),
        "status": "pending",
        "source": source,
        "origin": origin,
        "url": url,
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "attempts": 0,
        "extra": extra or {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Sherlockdogs clipping Codex job.")
    parser.add_argument("url", help="Source URL")
    parser.add_argument("task", nargs="*", help="Task text, for example: #ob 投资分析，重点看风险")
    parser.add_argument("--origin", default="manual", help="Where this job came from")
    parser.add_argument("--pending-dir", default=str(PENDING_DIR))
    parser.add_argument("--print-path", action="store_true")
    args = parser.parse_args()

    job = build_job(args.url, " ".join(args.task), args.origin)
    pending_dir = Path(args.pending_dir)
    pending_dir.mkdir(parents=True, exist_ok=True)
    path = pending_dir / f"{safe_id_part(job['job_id'], 64)}.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.print_path:
        print(path)
    else:
        print(json.dumps({"ok": True, "job_id": job["job_id"], "path": str(path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
