#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 /path/to/Sherlockdogs-Windows-Evidence-*" >&2
  exit 2
fi

latest_report=""
for root in "$@"; do
  if [[ -f "$root" ]]; then
    candidate="$root"
  elif [[ -d "$root" ]]; then
    candidate="$(
      find "$root" -type f \( \
        -name '*windows-wechat-db-smoke*.txt' \
        -o -path '*/windows-wechat-db-smoke/*.txt' \
        -o -name '*.txt' \
      \) -print0 | xargs -0 ls -t 2>/dev/null | head -n 1 || true
    )"
  else
    candidate=""
  fi
  if [[ -n "${candidate:-}" ]]; then
    latest_report="$candidate"
    break
  fi
done

if [[ -z "$latest_report" ]]; then
  echo "windows_wechat_db_verified=false"
  echo "windows_wechat_db_evidence=missing"
  exit 1
fi

required=(
  "token_match=ok"
  "windows_wechat_db=ok"
  "connect_wechat=ok"
  "self_chat_received=ok"
  "desktop_received=ok"
  "codex_job_created=ok"
  "codex_card=ok"
  "thread_completed=True"
)
for needle in "${required[@]}"; do
  if ! grep -q "$needle" "$latest_report"; then
    echo "windows_wechat_db_verified=false"
    echo "windows_wechat_db_evidence=invalid"
    echo "missing=$needle"
    echo "report=$latest_report"
    exit 1
  fi
done

echo "windows_wechat_db_verified=true"
echo "windows_wechat_db_evidence=$latest_report"
