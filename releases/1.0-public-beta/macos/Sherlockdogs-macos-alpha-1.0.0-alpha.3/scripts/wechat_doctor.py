#!/usr/bin/env python3
"""Diagnose and bind the Sherlockdogs personal WeChat receiver."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import personal_wechat_inbox as inbox  # noqa: E402


def human_time(ts: int) -> str:
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def message_summary(msg: dict[str, Any]) -> dict[str, Any]:
    text = inbox.message_text(msg)
    raw = str(msg.get("raw") or "")
    return {
        "chat_id": msg.get("chat_id", ""),
        "message_id": msg.get("id", ""),
        "timestamp": msg.get("timestamp", 0),
        "time": human_time(int(msg.get("timestamp") or 0)),
        "local_type": msg.get("local_type", 0),
        "title": msg.get("title", ""),
        "urls": msg.get("urls", []),
        "task": msg.get("task", ""),
        "has_image": bool((msg.get("image") or {}).get("source_path") or int(msg.get("local_type") or 0) == 3),
        "text_preview": (text or raw).replace("\n", " ")[:160],
        "raw_preview": raw.replace("\n", " ")[:240],
    }


def load_all_recent(receivers: list[str], lookback_seconds: int, limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    db = inbox.load_db()
    resolved: list[dict[str, Any]] = []
    messages: list[dict[str, Any]] = []
    since_ts = int(time.time()) - lookback_seconds
    for receiver in receivers:
        chat_id = db.resolve_username(receiver) or receiver
        account_dir = inbox.account_dir_for(receiver, chat_id)
        status = {"input": receiver, "chat_id": chat_id, "ok": True, "error": ""}
        try:
            fetched = inbox.fetch_messages(db, chat_id, since_ts=since_ts, limit=limit, account_dir=account_dir)
            messages.extend(fetched)
            status["messages"] = len(fetched)
        except Exception as exc:
            status["ok"] = False
            status["error"] = str(exc)
            status["messages"] = 0
        resolved.append(status)
    messages.sort(key=lambda item: int(item.get("timestamp") or 0), reverse=True)
    return resolved, messages, ""


def choose_bind_candidate(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for msg in messages:
        if msg.get("urls") or inbox.has_content(msg):
            return msg
    return messages[0] if messages else None


def write_receiver(chat_id: str) -> None:
    inbox.RECEIVER_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if inbox.RECEIVER_FILE.exists():
        existing = [
            line.strip()
            for line in inbox.RECEIVER_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    values = [chat_id] + [item for item in existing if item != chat_id and item != "filehelper"]
    if "filehelper" in existing:
        values.append("filehelper")
    inbox.RECEIVER_FILE.write_text("\n".join(values) + "\n", encoding="utf-8")


def diagnose(args: argparse.Namespace) -> dict[str, Any]:
    configured_receivers = inbox.load_receivers()
    receivers = args.receiver or configured_receivers
    result: dict[str, Any] = {
        "ok": False,
        "mode": "wechat_doctor",
        "receiver_file": str(inbox.RECEIVER_FILE),
        "configured_receivers": configured_receivers,
        "lookback_seconds": args.lookback_seconds,
        "checks": {},
        "resolved_receivers": [],
        "recent_messages": [],
        "bind_candidate": None,
        "actions": [],
    }

    try:
        resolved, messages, _ = load_all_recent(receivers, args.lookback_seconds, args.limit)
        result["checks"]["db_readable"] = True
        result["resolved_receivers"] = resolved
    except Exception as exc:
        result["checks"]["db_readable"] = False
        result["error"] = str(exc)
        result["actions"].append("Mac 微信数据库不可读：先确认 Mac 微信已登录，并运行现有 key/权限修复流程。")
        return result

    summarized = [message_summary(msg) for msg in messages[: args.show]]
    result["recent_messages"] = summarized
    result["checks"]["has_recent_message"] = bool(messages)
    result["checks"]["has_recognizable_content"] = any(inbox.has_content(msg) for msg in messages)
    result["checks"]["receiver_configured"] = bool(configured_receivers)

    candidate = choose_bind_candidate(messages)
    if candidate:
        result["bind_candidate"] = message_summary(candidate)

    if args.bind_latest:
        if not candidate:
            result["actions"].append("未找到可绑定的新消息。请用手机微信转发一条链接给自己，然后重试。")
        else:
            chat_id = str(candidate["chat_id"])
            write_receiver(chat_id)
            result["bound_receiver"] = chat_id
            result["actions"].append(f"已绑定微信接收会话：{chat_id}")

    if not messages:
        result["actions"].append("没有看到最近消息：确认 Mac 微信聊天列表里能看到刚发给自己的内容。")
    elif not result["checks"]["has_recognizable_content"]:
        result["actions"].append("看到了微信消息，但没有识别出链接、图片、文本或文件。")
    elif not args.bind_latest:
        result["actions"].append("如这是刚发给自己的测试消息，可用 --bind-latest 绑定为接收器。")

    result["ok"] = bool(result["checks"]["db_readable"])
    if args.require_bind and not result.get("bound_receiver"):
        result["ok"] = False
        result["actions"].append("本次未完成微信接收会话绑定，Personal Mode 未启用。")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Sherlockdogs personal WeChat receiver.")
    parser.add_argument("--receiver", action="append", help="Receiver username/chat id to inspect. Defaults to personal_receiver_chats.txt.")
    parser.add_argument("--lookback-seconds", type=int, default=10 * 60)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--show", type=int, default=10)
    parser.add_argument("--bind-latest", action="store_true", help="Bind the latest recognizable message chat as the receiver.")
    parser.add_argument("--require-bind", action="store_true", help="Exit non-zero unless --bind-latest binds a receiver.")
    args = parser.parse_args()

    result = diagnose(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
