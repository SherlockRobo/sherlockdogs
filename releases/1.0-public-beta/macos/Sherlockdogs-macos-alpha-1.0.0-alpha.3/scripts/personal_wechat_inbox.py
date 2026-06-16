#!/usr/bin/env python3
"""Poll personal Mac WeChat chats and create OB/Codex jobs from forwarded links."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import zstandard as zstd
from wechat_mcp_macos.config import load_config
from wechat_mcp_macos.db import WeChatDB
from wechat_mcp_macos.key_extractor import get_cached_keys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from create_job import PENDING_DIR, build_job, classify_url, now_iso as job_now_iso, parse_task, safe_id_part  # noqa: E402
from ingest_text import extract_explicit_task, extract_task, extract_title_hint  # noqa: E402
from sdogs_paths import JOBS_DIR, PROJECT_DIR, RUNS_DIR  # noqa: E402


STATE_FILE = JOBS_DIR / "personal_wechat_inbox_state.json"
RECEIVER_FILE = JOBS_DIR / "personal_receiver_chats.txt"
EVENT_LOG = RUNS_DIR / "personal-wechat-inbox.events.jsonl"
INBOX_EVENTS_DIR = JOBS_DIR / "inbox-events"

DEFAULT_RECEIVERS = ["mvettel", "filehelper"]
TASK_WINDOW_SECONDS = 60
BUNDLE_WINDOW_SECONDS = 60
POLL_LOOKBACK_SECONDS = 30 * 60
SETTLE_SECONDS = 15
POLL_TIMEOUT_SECONDS = 45
SUPPORTED_SOURCES = {"wechat", "x", "xhs", "bilibili", "youtube", "tiktok", "douyin"}
URL_RE = re.compile(r"https?://[^\s<>'\"）)]+")
XML_URL_RE = re.compile(r"<url>(.*?)</url>", re.DOTALL | re.IGNORECASE)
XML_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
IMAGE_ATTR_RE = re.compile(r'([a-zA-Z0-9_]+)="([^"]*)"')
IMAGE_KEY_RE = re.compile(rb"[0-9a-f]{32}")
TASK_RE = re.compile(r"(?im)^\s*(#(?:[1-5]\b.*|ob\b.*|))\s*$")
_zstd_dctx = zstd.ZstdDecompressor()
_rwtemp_cache: dict[tuple[str, str], list[tuple[int, Path]]] = {}


class PollTimeout(TimeoutError):
    pass


def raise_poll_timeout(signum: int, frame: Any) -> None:
    raise PollTimeout("personal WeChat poll timed out")


KNOWN_MESSAGE_DBS = {
    "mvettel": (
        "message/message_3.db",
        "Msg_36aa6b614fcf5aa9d1b548f6b436658d",
    ),
    "filehelper": (
        "message/message_3.db",
        "Msg_9e20f478899dc29eb19741386f9343c8",
    ),
}
KNOWN_ACCOUNT_DIRS = {
    "mvettel": Path("/Users/bytedance/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/mvettel_6c03"),
}


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


def event_id_for_group(group: list[dict[str, Any]]) -> str:
    body = "\n".join(str(msg.get("id") or "") for msg in group)
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()[:16]


def write_inbox_event(group: list[dict[str, Any]], task: str, jobs: list[dict[str, Any]], dry_run: bool) -> dict[str, Any]:
    """Write a normalized Sherlockdogs Inbox event beside legacy job output.

    This is the bridge toward a single pipeline. Existing微信 job behavior stays
    unchanged; the event is an auditable adapter-layer artifact.
    """
    if not group:
        return {}
    payload = build_bundle_payload(group)
    event_id = f"wechat-{event_id_for_group(group)}"
    task_level, normalized_task, original_task = parse_task(task)
    title_hint = (
        str(group[0].get("title") or "").strip()
        or str((jobs[0] or {}).get("title") or "").strip()
        or title_for_bundle(payload, group)
    )
    event = {
        "version": 1,
        "event_id": event_id,
        "status": "received",
        "adapter": "personal-wechat-local-db",
        "origin": "personal-wechat-self-chat",
        "receiver_chat": group[0]["chat_id"],
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "title": title_hint,
        "created_at": job_now_iso(),
        "message": {
            "message_id": group[0]["id"],
            "message_ids": [msg["id"] for msg in group],
            "timestamp": payload["timestamp"],
            "timestamp_end": payload["timestamp_end"],
        },
        "payload": payload,
        "jobs": jobs,
    }
    if not dry_run:
        INBOX_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        path = INBOX_EVENTS_DIR / f"{event_id}.json"
        path.write_text(json.dumps(event, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        event["path"] = str(path)
    return event


def load_receivers() -> list[str]:
    if not RECEIVER_FILE.exists():
        RECEIVER_FILE.write_text("\n".join(DEFAULT_RECEIVERS) + "\n", encoding="utf-8")
    receivers = []
    for line in RECEIVER_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            receivers.append(line)
    return receivers or DEFAULT_RECEIVERS


def clean_url(url: str) -> str:
    return html.unescape(url).rstrip(".,，。;；!！?？)]}」』”")


def extract_urls(raw: str) -> list[str]:
    urls: list[str] = []
    for match in XML_URL_RE.findall(raw or ""):
        url = clean_url(match.strip())
        if url and url not in urls:
            urls.append(url)
    for match in URL_RE.findall(raw or ""):
        url = clean_url(match)
        if url and url not in urls:
            urls.append(url)
    return urls


def extract_title(raw: str) -> str:
    match = XML_TITLE_RE.search(raw or "")
    return html.unescape(match.group(1).strip()) if match else ""


def decode_content(content: Any, ct: Any) -> str:
    if ct and ct == 4 and isinstance(content, bytes):
        return _zstd_dctx.decompress(content).decode("utf-8", errors="replace")
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content or ""


def message_id(chat_id: str, ts: int, local_type: int, raw: str) -> str:
    body = f"{chat_id}\n{ts}\n{local_type}\n{raw[:500]}"
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()


def strip_task_lines(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        if TASK_RE.match(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def extract_image_attrs(raw: str) -> dict[str, str]:
    if "<img" not in (raw or ""):
        return {}
    return {key: html.unescape(value) for key, value in IMAGE_ATTR_RE.findall(raw)}


def extract_image_key(packed_info_data: Any) -> str:
    if not isinstance(packed_info_data, bytes):
        return ""
    matches = IMAGE_KEY_RE.findall(packed_info_data)
    return matches[-1].decode("ascii") if matches else ""


def table_attach_id(table_name: str) -> str:
    return table_name.removeprefix("Msg_")


def is_decoded_image(path: Path) -> bool:
    try:
        head = path.read_bytes()[:16]
    except Exception:
        return False
    return (
        head.startswith(b"\xff\xd8\xff")
        or head.startswith(b"\x89PNG")
        or (head.startswith(b"RIFF") and b"WEBP" in head)
    )


def find_rwtemp_image(account_dir: Path, ts: int, window_seconds: int = 30 * 60) -> str:
    month = datetime.fromtimestamp(ts).strftime("%Y-%m")
    root = account_dir / "temp" / "RWTemp" / month
    if not root.exists():
        return ""
    cache_key = (str(account_dir), month)
    if cache_key not in _rwtemp_cache:
        month_images: list[tuple[int, Path]] = []
        for path in root.glob("*/*"):
            if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            try:
                mtime = int(path.stat().st_mtime)
            except OSError:
                continue
            if is_decoded_image(path):
                month_images.append((mtime, path))
        _rwtemp_cache[cache_key] = month_images
    candidates = [(abs(mtime - ts), path) for mtime, path in _rwtemp_cache[cache_key] if abs(mtime - ts) <= window_seconds]
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0])
    return str(candidates[0][1])


def detect_image_path(account_dir: Path | None, attach_id: str, ts: int, key: str) -> str:
    if not account_dir or not attach_id or not key:
        return ""
    month = datetime.fromtimestamp(ts).strftime("%Y-%m")
    img_dir = account_dir / "msg" / "attach" / attach_id / month / "Img"
    for suffix in ("_h.dat", ".dat", "_t.dat"):
        path = img_dir / f"{key}{suffix}"
        if path.exists() and is_decoded_image(path):
            return str(path)
    return find_rwtemp_image(account_dir, ts)


def load_db() -> WeChatDB:
    cfg = load_config()
    keys = get_cached_keys()
    if not keys:
        raise RuntimeError("WeChat keys missing; run key extraction first")
    return WeChatDB(cfg["db_dir"], keys)


def default_account_dir() -> Path | None:
    try:
        db_dir = Path(load_config()["db_dir"])
    except Exception:
        return None
    if db_dir.name == "db_storage":
        return db_dir.parent
    return None


def account_dir_for(receiver: str, chat_id: str) -> Path | None:
    return KNOWN_ACCOUNT_DIRS.get(receiver) or KNOWN_ACCOUNT_DIRS.get(chat_id) or default_account_dir()


def fetch_messages(
    db: WeChatDB,
    chat_id: str,
    since_ts: int,
    limit: int,
    account_dir: Path | None = None,
) -> list[dict[str, Any]]:
    now_ceiling = int(time.time()) + 300
    if chat_id in KNOWN_MESSAGE_DBS:
        rel_path, table_name = KNOWN_MESSAGE_DBS[chat_id]
        db_path = db._get_decrypted_db(rel_path)
        db_targets = [(db_path, table_name)]
    else:
        db_path, table_name = db._find_msg_table(chat_id)
        db_targets = [(db_path, table_name)] if db_path and table_name else []
    if not db_path or not table_name:
        return []

    query = f"""
        SELECT local_type, create_time, message_content, WCDB_CT_message_content, packed_info_data
        FROM [{table_name}]
        WHERE create_time > ? AND create_time <= ?
        ORDER BY create_time ASC
        LIMIT ?
    """
    rows = []
    for target_path, target_table in db_targets:
        for attempt in range(2):
            conn = sqlite3.connect(target_path)
            try:
                rows.extend(conn.execute(query, (since_ts, now_ceiling, limit)).fetchall())
                break
            except sqlite3.DatabaseError as exc:
                conn.close()
                if attempt == 0 and "malformed" in str(exc).lower() and chat_id in KNOWN_MESSAGE_DBS:
                    Path(target_path).unlink(missing_ok=True)
                    target_path = db._get_decrypted_db(KNOWN_MESSAGE_DBS[chat_id][0])
                    continue
                raise
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
    rows.sort(key=lambda row: int(row[1]))

    messages = []
    attach_id = table_attach_id(table_name)
    for local_type, create_time, content, ct, packed_info_data in rows:
        raw = decode_content(content, ct)
        if not raw:
            continue
        image_key = extract_image_key(packed_info_data)
        messages.append(
            {
                "chat_id": chat_id,
                "local_type": int(local_type),
                "timestamp": int(create_time),
                "raw": raw,
                "title": extract_title(raw),
                "urls": extract_urls(raw),
                "task": extract_explicit_task(raw),
                "image": {
                    "key": image_key,
                    "attrs": extract_image_attrs(raw) if int(local_type) == 3 else {},
                    "source_path": detect_image_path(account_dir, attach_id, int(create_time), image_key)
                    if int(local_type) == 3
                    else "",
                },
                "id": message_id(chat_id, int(create_time), int(local_type), raw),
            }
        )
    return messages


def best_task_for_link(link_msg: dict[str, Any], tasks: list[dict[str, Any]], state: dict[str, Any]) -> str:
    if link_msg.get("task"):
        return str(link_msg["task"])
    candidates = [
        t
        for t in tasks
        if t.get("chat_id") == link_msg.get("chat_id")
        and int(link_msg["timestamp"]) <= int(t["timestamp"]) <= int(link_msg["timestamp"]) + TASK_WINDOW_SECONDS
    ]
    if candidates:
        candidates.sort(key=lambda t: int(t["timestamp"]))
        return str(candidates[0]["task"])

    return extract_task("")


def create_jobs(link_msg: dict[str, Any], task: str, dry_run: bool) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    title_hint = link_msg.get("title", "") or extract_title_hint(link_msg.get("raw", ""))
    for url in link_msg["urls"]:
        source = classify_url(url)
        if source not in SUPPORTED_SOURCES:
            continue
        job = build_job(
            url,
            task,
            "personal-wechat-self-chat",
            extra={
                "inbox": "personal-wechat-local-db",
                "receiver_chat": link_msg["chat_id"],
                "message_id": link_msg["id"],
                "message_timestamp": link_msg["timestamp"],
                "title": title_hint,
                "raw_preview": link_msg["raw"][:3000],
            },
        )
        path = PENDING_DIR / f"{safe_id_part(job['job_id'], 64)}.json"
        if not dry_run:
            path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        jobs.append({"job_id": job["job_id"], "source": source, "url": url, "task": job["task"], "path": str(path)})
    return jobs


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def message_text(msg: dict[str, Any]) -> str:
    if int(msg.get("local_type") or 0) != 1:
        return ""
    return strip_task_lines(msg.get("raw", ""))


def has_content(msg: dict[str, Any]) -> bool:
    if msg.get("urls"):
        return True
    if int(msg.get("local_type") or 0) == 3:
        return True
    return bool(message_text(msg))


def group_id(messages: list[dict[str, Any]]) -> str:
    body = "\n".join(str(m.get("id") or "") for m in messages)
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()


def build_message_groups(messages: list[dict[str, Any]], seen: set[str]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for msg in messages:
        if msg["id"] in seen or not has_content(msg):
            continue
        if (
            current
            and msg["chat_id"] == current[-1]["chat_id"]
            and int(msg["timestamp"]) - int(current[-1]["timestamp"]) <= BUNDLE_WINDOW_SECONDS
        ):
            current.append(msg)
            continue
        if current:
            groups.append(current)
        current = [msg]
    if current:
        groups.append(current)
    return groups


def should_use_bundle(group: list[dict[str, Any]]) -> bool:
    if len(group) > 1:
        return True
    msg = group[0]
    return not msg.get("urls")


def build_bundle_payload(group: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [message_text(msg) for msg in group if message_text(msg)]
    urls = unique_values([url for msg in group for url in msg.get("urls", [])])
    images = [msg.get("image") for msg in group if int(msg.get("local_type") or 0) == 3]
    images = [image for image in images if isinstance(image, dict)]
    raw_messages = [
        {
            "message_id": msg["id"],
            "timestamp": msg["timestamp"],
            "local_type": msg["local_type"],
            "title": msg.get("title", ""),
            "urls": msg.get("urls", []),
            "text": message_text(msg),
            "image": msg.get("image") if int(msg.get("local_type") or 0) == 3 else {},
            "raw_preview": msg.get("raw", "")[:3000],
        }
        for msg in group
    ]
    if urls and (texts or images or len(group) > 1):
        kind = "bundle"
    elif images:
        kind = "image"
    else:
        kind = "text"
    return {
        "kind": kind,
        "chat_id": group[0]["chat_id"],
        "message_id": group[0]["id"],
        "message_ids": [msg["id"] for msg in group],
        "timestamp": min(int(msg["timestamp"]) for msg in group),
        "timestamp_end": max(int(msg["timestamp"]) for msg in group),
        "text": "\n\n".join(texts),
        "urls": urls,
        "primary_url": urls[0] if urls else "",
        "image": images[0] if images else {},
        "images": images,
        "raw_messages": raw_messages,
        "raw_preview": "\n\n---\n\n".join(str(msg.get("raw", ""))[:3000] for msg in group),
    }


def title_for_bundle(payload: dict[str, Any], group: list[dict[str, Any]]) -> str:
    title_hint = extract_title_hint(str(payload.get("text") or ""))
    if title_hint:
        return title_hint
    for msg in group:
        title = str(msg.get("title") or "").strip()
        if title:
            return title[:120]
    if payload.get("primary_url"):
        return str(payload["primary_url"])[:120]
    if payload.get("images"):
        return "微信图片剪藏"
    return "微信剪藏"


def build_inbox_job_from_group(group: list[dict[str, Any]], task: str) -> dict[str, Any]:
    task_level, normalized_task, original_task = parse_task(task)
    payload = build_bundle_payload(group)
    digest = group_id(group)
    url = f"wechat://personal/{group[0]['chat_id']}/{digest}"
    created_at = job_now_iso()
    title_hint = title_for_bundle(payload, group)
    return {
        "version": 1,
        "job_id": f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-wechat-inbox-{digest[:10]}",
        "status": "pending",
        "source": "wechat_inbox",
        "origin": "personal-wechat-self-chat",
        "url": url,
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "created_at": created_at,
        "updated_at": created_at,
        "attempts": 0,
        "extra": {
            "inbox": "personal-wechat-local-db",
            "receiver_chat": group[0]["chat_id"],
            "message_id": group[0]["id"],
            "message_ids": [msg["id"] for msg in group],
            "message_timestamp": payload["timestamp"],
            "title": title_hint,
            "payload": payload,
        },
    }


def build_inbox_job(msg: dict[str, Any], task: str) -> dict[str, Any]:
    return build_inbox_job_from_group([msg], task)


def create_inbox_job_for_group(group: list[dict[str, Any]], task: str, dry_run: bool) -> dict[str, Any] | None:
    if not group:
        return None
    if not any(has_content(msg) for msg in group):
        return None
    job = build_inbox_job_from_group(group, task)
    path = PENDING_DIR / f"{safe_id_part(job['job_id'], 64)}.json"
    if not dry_run:
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "job_id": job["job_id"],
        "source": "wechat_inbox",
        "url": job["url"],
        "task": job["task"],
        "path": str(path),
        "kind": job["extra"]["payload"]["kind"],
    }


def create_inbox_job(msg: dict[str, Any], task: str, dry_run: bool) -> dict[str, Any] | None:
    return create_inbox_job_for_group([msg], task, dry_run)


def run_once(limit: int, dry_run: bool, settle_seconds: int) -> dict[str, Any]:
    db = load_db()
    state = read_json(STATE_FILE, {})
    seen = set(state.get("seen_message_ids") or [])
    receivers = load_receivers()
    resolved = []
    all_messages: list[dict[str, Any]] = []

    for receiver in receivers:
        chat_id = db.resolve_username(receiver) or receiver
        resolved.append({"input": receiver, "chat_id": chat_id})
        since_ts = int(state.get("last_ts_by_chat", {}).get(chat_id) or (time.time() - POLL_LOOKBACK_SECONDS))
        account_dir = account_dir_for(receiver, chat_id)
        all_messages.extend(fetch_messages(db, chat_id, since_ts=since_ts, limit=limit, account_dir=account_dir))

    if not all_messages:
        return {"ok": True, "processed": 0, "receivers": resolved}

    all_messages.sort(key=lambda m: (m["timestamp"], m["id"]))
    cutoff_ts = int(time.time()) - settle_seconds
    recent_count = sum(1 for m in all_messages if int(m["timestamp"]) > cutoff_ts)
    all_messages = [m for m in all_messages if int(m["timestamp"]) <= cutoff_ts]
    if not all_messages:
        return {"ok": True, "processed": 0, "recent_waiting": recent_count, "receivers": resolved}
    tasks = [m for m in all_messages if m["task"]]
    for task_msg in tasks:
        state["last_task"] = task_msg["task"]
        state["last_task_ts"] = task_msg["timestamp"]

    results = []
    last_ts_by_chat = dict(state.get("last_ts_by_chat") or {})
    groups = build_message_groups(all_messages, seen)
    for group in groups:
        for msg in group:
            last_ts_by_chat[msg["chat_id"]] = max(int(last_ts_by_chat.get(msg["chat_id"], 0)), int(msg["timestamp"]))
            seen.add(msg["id"])
        task = best_task_for_link(group[-1], tasks, state)
        if should_use_bundle(group):
            inbox_job = create_inbox_job_for_group(group, task=task, dry_run=dry_run)
            jobs = [inbox_job] if inbox_job else []
            source_urls = unique_values([url for msg in group for url in msg.get("urls", [])])
        else:
            jobs = create_jobs(group[0], task=task, dry_run=dry_run)
            source_urls = group[0].get("urls", [])
            if not jobs and has_content(group[0]):
                inbox_job = create_inbox_job_for_group(group, task=task, dry_run=dry_run)
                jobs = [inbox_job] if inbox_job else []
        if not jobs:
            continue
        normalized_event = write_inbox_event(group, task=task, jobs=jobs, dry_run=dry_run)
        event = {
            "message_id": group[0]["id"],
            "message_ids": [msg["id"] for msg in group],
            "chat_id": group[0]["chat_id"],
            "timestamp": group[0]["timestamp"],
            "timestamp_end": group[-1]["timestamp"],
            "title": group[0].get("title", ""),
            "urls": source_urls,
            "jobs": jobs,
            "inbox_event": {
                "event_id": normalized_event.get("event_id", ""),
                "path": normalized_event.get("path", ""),
            },
        }
        results.append(event)
        if not dry_run:
            append_event(event)

    for msg in all_messages:
        last_ts_by_chat[msg["chat_id"]] = max(int(last_ts_by_chat.get(msg["chat_id"], 0)), int(msg["timestamp"]))
        seen.add(msg["id"])

    state["seen_message_ids"] = sorted(seen)[-1000:]
    state["last_ts_by_chat"] = last_ts_by_chat
    state["last_seen_at"] = now_iso()
    if not dry_run:
        write_json(STATE_FILE, state)

    return {"ok": True, "processed": len(results), "receivers": resolved, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create OB/Codex jobs from personal WeChat self-chat forwards.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=20.0)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--settle-seconds", type=int, default=SETTLE_SECONDS)
    parser.add_argument("--poll-timeout", type=int, default=POLL_TIMEOUT_SECONDS)
    args = parser.parse_args()

    while True:
        try:
            signal.signal(signal.SIGALRM, raise_poll_timeout)
            signal.alarm(max(1, int(args.poll_timeout)))
            try:
                result = run_once(limit=args.limit, dry_run=args.dry_run, settle_seconds=args.settle_seconds)
            finally:
                signal.alarm(0)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc), "ts": now_iso()}, ensure_ascii=False), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
