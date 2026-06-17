#!/usr/bin/env python3
"""Poll decrypted Windows WeChat message DBs and create Sherlockdogs jobs.

This adapter intentionally starts at the decrypted DB boundary. The Windows
Connect script binds a local decrypted WeChat DB root, then this poller turns
new self-chat messages into the same job shape as the macOS adapter.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import zstandard as zstd
except Exception:  # pragma: no cover - optional on schema variants.
    zstd = None

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from create_job import PENDING_DIR, build_job, classify_url, now_iso as job_now_iso, parse_task, safe_id_part  # noqa: E402
from ingest_text import extract_explicit_task, extract_task, extract_title_hint  # noqa: E402
from sdogs_paths import JOBS_DIR, RUNS_DIR  # noqa: E402


STATE_FILE = JOBS_DIR / "windows_wechat_inbox_state.json"
RECEIVER_FILE = JOBS_DIR / "windows_receiver_chats.txt"
EVENT_LOG = RUNS_DIR / "windows-wechat-inbox.events.jsonl"
INBOX_EVENTS_DIR = JOBS_DIR / "inbox-events"

DEFAULT_RECEIVERS = ["filehelper"]
TASK_WINDOW_SECONDS = 60
BUNDLE_WINDOW_SECONDS = 60
POLL_LOOKBACK_SECONDS = 30 * 60
SETTLE_SECONDS = 15
SUPPORTED_SOURCES = {"wechat", "x", "xhs", "bilibili", "youtube", "tiktok", "douyin", "web"}
URL_RE = re.compile(r"https?://[^\s<>'\"）)]+")
XML_URL_RE = re.compile(r"<url>(.*?)</url>", re.DOTALL | re.IGNORECASE)
XML_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
IMAGE_ATTR_RE = re.compile(r'([a-zA-Z0-9_]+)="([^"]*)"')
TASK_RE = re.compile(r"(?im)^\s*(#(?:[1-5]\b.*|ob\b.*|))\s*$")
ZSTD_DCTX = zstd.ZstdDecompressor() if zstd else None


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


def strip_task_lines(text: str) -> str:
    lines = []
    for line in (text or "").splitlines():
        if TASK_RE.match(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def decode_content(content: Any, ct: Any = None) -> str:
    if isinstance(content, bytes):
        if ct and int(ct) == 4 and ZSTD_DCTX:
            try:
                return ZSTD_DCTX.decompress(content).decode("utf-8", errors="replace")
            except Exception:
                pass
        return content.decode("utf-8", errors="replace")
    return str(content or "")


def read_receivers(path: Path = RECEIVER_FILE) -> list[str]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(DEFAULT_RECEIVERS) + "\n", encoding="utf-8")
    receivers = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            receivers.append(line)
    return receivers or DEFAULT_RECEIVERS


def db_root_from_args(arg_root: str) -> Path:
    raw = arg_root or ""
    if not raw:
        raw = (
            sys.platform == "win32"
            and __import__("os").environ.get("SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR", "")
            or __import__("os").environ.get("SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR", "")
        )
    if not raw:
        raw = str(Path.home() / ".sherlockdogs" / "windows-wechat-decrypted")
    return Path(raw).expanduser()


def discover_message_dbs(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    patterns = [
        "message/message_*.db",
        "message/*.db",
        "**/message_*.db",
        "**/MSG*.db",
        "**/Msg*.db",
    ]
    found: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and path.suffix.lower() == ".db" and path not in found:
                found.append(path)
    return sorted(found, key=lambda p: str(p).lower())


def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [str(row[0]) for row in rows]
    preferred = [name for name in names if name.lower().startswith("msg")]
    return preferred or names


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info([{table}])").fetchall()}


def first_col(columns: set[str], choices: list[str]) -> str:
    lowered = {col.lower(): col for col in columns}
    for choice in choices:
        if choice.lower() in lowered:
            return lowered[choice.lower()]
    return ""


def message_id(db_path: Path, table: str, ts: int, local_type: int, raw: str) -> str:
    body = f"{db_path.name}\n{table}\n{ts}\n{local_type}\n{raw[:500]}"
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()


def normalized_table_id(table: str) -> str:
    return re.sub(r"^msg[_-]?", "", table or "", flags=re.IGNORECASE)


def read_messages_from_table(
    conn: sqlite3.Connection,
    db_path: Path,
    table: str,
    since_ts: int,
    limit: int,
    receivers: set[str],
) -> list[dict[str, Any]]:
    columns = table_columns(conn, table)
    time_col = first_col(columns, ["create_time", "CreateTime", "createTime", "timestamp", "time"])
    content_col = first_col(columns, ["message_content", "StrContent", "content", "Content", "msgContent"])
    type_col = first_col(columns, ["local_type", "Type", "type", "MsgType"])
    compress_col = first_col(columns, ["WCDB_CT_message_content", "CompressContent", "content_compress"])
    sender_col = first_col(columns, ["talker", "Talker", "StrTalker", "UserName", "username", "chat_id"])
    if not time_col or not content_col:
        return []

    select_cols = [time_col, content_col]
    select_cols.append(type_col or "NULL")
    select_cols.append(compress_col or "NULL")
    select_cols.append(sender_col or "NULL")
    where = f"[{time_col}] > ? AND [{time_col}] <= ?"
    now_ceiling = int(time.time()) + 300
    sql = f"SELECT {', '.join(f'[{c}]' if c != 'NULL' else 'NULL' for c in select_cols)} FROM [{table}] WHERE {where} ORDER BY [{time_col}] ASC LIMIT ?"
    try:
        rows = conn.execute(sql, (since_ts, now_ceiling, limit)).fetchall()
    except sqlite3.DatabaseError:
        return []

    messages: list[dict[str, Any]] = []
    for create_time, content, local_type, ct, talker in rows:
        chat_id = str(talker or table)
        if receivers and "*" not in receivers:
            haystack = {chat_id, table, normalized_table_id(table)}
            if not (haystack & receivers):
                continue
        raw = decode_content(content, ct)
        if not raw:
            continue
        local_type_int = int(local_type or 1)
        ts = int(create_time)
        messages.append(
            {
                "chat_id": chat_id,
                "table": table,
                "db": str(db_path),
                "local_type": local_type_int,
                "timestamp": ts,
                "raw": raw,
                "title": extract_title(raw),
                "urls": extract_urls(raw),
                "task": extract_explicit_task(raw),
                "image": {"key": "", "attrs": extract_image_attrs(raw) if local_type_int == 3 else {}, "source_path": ""},
                "id": message_id(db_path, table, ts, local_type_int, raw),
            }
        )
    return messages


def extract_image_attrs(raw: str) -> dict[str, str]:
    if "<img" not in (raw or ""):
        return {}
    return {key: html.unescape(value) for key, value in IMAGE_ATTR_RE.findall(raw)}


def fetch_messages(root: Path, since_ts_by_chat: dict[str, int], limit: int, receivers: list[str]) -> list[dict[str, Any]]:
    receiver_set = {r.strip() for r in receivers if r.strip()}
    messages: list[dict[str, Any]] = []
    for db_path in discover_message_dbs(root):
        try:
            conn = sqlite3.connect(db_path)
        except sqlite3.DatabaseError:
            continue
        try:
            for table in table_names(conn):
                since_ts = int(since_ts_by_chat.get(table) or (time.time() - POLL_LOOKBACK_SECONDS))
                messages.extend(read_messages_from_table(conn, db_path, table, since_ts, limit, receiver_set))
        finally:
            conn.close()
    messages.sort(key=lambda m: (int(m["timestamp"]), m["id"]))
    return messages


def message_text(msg: dict[str, Any]) -> str:
    if int(msg.get("local_type") or 0) != 1:
        return ""
    return strip_task_lines(msg.get("raw", ""))


def has_content(msg: dict[str, Any]) -> bool:
    return bool(msg.get("urls") or message_text(msg) or int(msg.get("local_type") or 0) == 3)


def unique_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def group_id(messages: list[dict[str, Any]]) -> str:
    body = "\n".join(str(m.get("id") or "") for m in messages)
    return hashlib.sha1(body.encode("utf-8", errors="replace")).hexdigest()


def build_message_groups(messages: list[dict[str, Any]], seen: set[str]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for msg in messages:
        if msg["id"] in seen or not has_content(msg):
            continue
        if current and msg["chat_id"] == current[-1]["chat_id"] and int(msg["timestamp"]) - int(current[-1]["timestamp"]) <= BUNDLE_WINDOW_SECONDS:
            current.append(msg)
            continue
        if current:
            groups.append(current)
        current = [msg]
    if current:
        groups.append(current)
    return groups


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


def should_use_bundle(group: list[dict[str, Any]]) -> bool:
    if len(group) > 1:
        return True
    return not group[0].get("urls")


def create_link_jobs(group: list[dict[str, Any]], task: str, dry_run: bool) -> list[dict[str, Any]]:
    msg = group[0]
    jobs: list[dict[str, Any]] = []
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    title_hint = msg.get("title", "") or extract_title_hint(msg.get("raw", ""))
    for url in msg["urls"]:
        source = classify_url(url)
        if source not in SUPPORTED_SOURCES:
            continue
        job = build_job(
            url,
            task,
            "windows-wechat-self-chat",
            extra={
                "inbox": "windows-wechat-local-db",
                "receiver_chat": msg["chat_id"],
                "message_id": msg["id"],
                "message_timestamp": msg["timestamp"],
                "title": title_hint,
                "raw_preview": msg["raw"][:3000],
            },
        )
        path = PENDING_DIR / f"{safe_id_part(job['job_id'], 64)}.json"
        if not dry_run:
            path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        jobs.append({"job_id": job["job_id"], "source": source, "url": url, "task": job["task"], "path": str(path)})
    return jobs


def create_inbox_job_for_group(group: list[dict[str, Any]], task: str, dry_run: bool) -> dict[str, Any] | None:
    if not group:
        return None
    task_level, normalized_task, original_task = parse_task(task)
    payload = build_bundle_payload(group)
    digest = group_id(group)
    url = f"wechat://windows/{group[0]['chat_id']}/{digest}"
    created_at = job_now_iso()
    title_hint = title_for_bundle(payload, group)
    job = {
        "version": 1,
        "job_id": f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-wechat-inbox-{digest[:10]}",
        "status": "pending",
        "source": "wechat_inbox",
        "origin": "windows-wechat-self-chat",
        "url": url,
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "created_at": created_at,
        "updated_at": created_at,
        "attempts": 0,
        "extra": {
            "inbox": "windows-wechat-local-db",
            "receiver_chat": group[0]["chat_id"],
            "message_id": group[0]["id"],
            "message_ids": [msg["id"] for msg in group],
            "message_timestamp": payload["timestamp"],
            "title": title_hint,
            "payload": payload,
        },
    }
    path = PENDING_DIR / f"{safe_id_part(job['job_id'], 64)}.json"
    if not dry_run:
        path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"job_id": job["job_id"], "source": "wechat_inbox", "url": job["url"], "task": job["task"], "path": str(path), "kind": payload["kind"]}


def best_task_for_group(group: list[dict[str, Any]], tasks: list[dict[str, Any]], state: dict[str, Any]) -> str:
    for msg in group:
        if msg.get("task"):
            return str(msg["task"])
    last = group[-1]
    candidates = [
        t
        for t in tasks
        if t.get("chat_id") == last.get("chat_id")
        and int(last["timestamp"]) <= int(t["timestamp"]) <= int(last["timestamp"]) + TASK_WINDOW_SECONDS
    ]
    if candidates:
        candidates.sort(key=lambda t: int(t["timestamp"]))
        return str(candidates[0]["task"])
    return str(state.get("last_task") or extract_task(""))


def write_inbox_event(group: list[dict[str, Any]], task: str, jobs: list[dict[str, Any]], dry_run: bool) -> dict[str, Any]:
    payload = build_bundle_payload(group)
    event_id = f"wechat-windows-{group_id(group)[:16]}"
    task_level, normalized_task, original_task = parse_task(task)
    event = {
        "version": 1,
        "event_id": event_id,
        "status": "received",
        "adapter": "windows-wechat-local-db",
        "origin": "windows-wechat-self-chat",
        "receiver_chat": group[0]["chat_id"],
        "task": normalized_task,
        "task_original": original_task,
        "task_level": task_level,
        "title": title_for_bundle(payload, group),
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


def run_once(root: Path, limit: int, dry_run: bool, settle_seconds: int, receivers_override: str = "") -> dict[str, Any]:
    state = read_json(STATE_FILE, {})
    seen = set(state.get("seen_message_ids") or [])
    receivers = [item.strip() for item in receivers_override.split(",") if item.strip()] if receivers_override else read_receivers()
    last_ts_by_chat = dict(state.get("last_ts_by_chat") or {})
    messages = fetch_messages(root, last_ts_by_chat, limit, receivers)
    if not messages:
        return {"ok": True, "processed": 0, "db_root": str(root), "receivers": receivers}
    cutoff_ts = int(time.time()) - settle_seconds
    recent_count = sum(1 for msg in messages if int(msg["timestamp"]) > cutoff_ts)
    messages = [msg for msg in messages if int(msg["timestamp"]) <= cutoff_ts]
    if not messages:
        return {"ok": True, "processed": 0, "recent_waiting": recent_count, "db_root": str(root), "receivers": receivers}

    tasks = [m for m in messages if m["task"]]
    for task_msg in tasks:
        state["last_task"] = task_msg["task"]
        state["last_task_ts"] = task_msg["timestamp"]

    groups = build_message_groups(messages, seen)
    results = []
    for group in groups:
        for msg in group:
            last_ts_by_chat[msg["chat_id"]] = max(int(last_ts_by_chat.get(msg["chat_id"], 0)), int(msg["timestamp"]))
            seen.add(msg["id"])
        task = best_task_for_group(group, tasks, state)
        if should_use_bundle(group):
            inbox_job = create_inbox_job_for_group(group, task, dry_run)
            jobs = [inbox_job] if inbox_job else []
            source_urls = unique_values([url for msg in group for url in msg.get("urls", [])])
        else:
            jobs = create_link_jobs(group, task, dry_run)
            source_urls = group[0].get("urls", [])
            if not jobs and has_content(group[0]):
                inbox_job = create_inbox_job_for_group(group, task, dry_run)
                jobs = [inbox_job] if inbox_job else []
        if not jobs:
            continue
        normalized_event = write_inbox_event(group, task, jobs, dry_run)
        event = {
            "message_id": group[0]["id"],
            "message_ids": [msg["id"] for msg in group],
            "chat_id": group[0]["chat_id"],
            "timestamp": group[0]["timestamp"],
            "timestamp_end": group[-1]["timestamp"],
            "title": group[0].get("title", ""),
            "urls": source_urls,
            "jobs": jobs,
            "inbox_event": {"event_id": normalized_event.get("event_id", ""), "path": normalized_event.get("path", "")},
        }
        results.append(event)
        if not dry_run:
            append_event(event)

    for msg in messages:
        last_ts_by_chat[msg["chat_id"]] = max(int(last_ts_by_chat.get(msg["chat_id"], 0)), int(msg["timestamp"]))
        seen.add(msg["id"])
    state["seen_message_ids"] = sorted(seen)[-1000:]
    state["last_ts_by_chat"] = last_ts_by_chat
    state["last_seen_at"] = now_iso()
    if not dry_run:
        write_json(STATE_FILE, state)
    return {"ok": True, "processed": len(results), "db_root": str(root), "receivers": receivers, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create OB/Codex jobs from decrypted Windows WeChat self-chat DBs.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=20.0)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--db-root", default="")
    parser.add_argument("--receivers", default="", help="Comma-separated receiver chats. Use * to scan all chats for smoke discovery.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--settle-seconds", type=int, default=SETTLE_SECONDS)
    args = parser.parse_args()

    root = db_root_from_args(args.db_root)
    if not root.exists():
        print(json.dumps({"ok": False, "error": "windows WeChat decrypted DB root missing", "db_root": str(root)}, ensure_ascii=False), file=sys.stderr)
        return 1 if args.once else 0
    while True:
        try:
            result = run_once(root=root, limit=args.limit, dry_run=args.dry_run, settle_seconds=args.settle_seconds, receivers_override=args.receivers)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc), "ts": now_iso(), "db_root": str(root)}, ensure_ascii=False), file=sys.stderr, flush=True)
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
