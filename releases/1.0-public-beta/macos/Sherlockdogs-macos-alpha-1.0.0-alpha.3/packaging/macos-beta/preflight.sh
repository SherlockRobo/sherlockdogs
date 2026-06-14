#!/usr/bin/env bash
set -u

CONFIG_DIR="$HOME/.sherlockdogs"
INBOX_DIR="${SHERLOCKDOGS_INBOX_DIR:-$HOME/Sherlockdogs/Inbox}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
fail_count=0
warn_count=0

mark_fail() {
  echo "FAIL $1"
  fail_count=$((fail_count + 1))
}

mark_warn() {
  echo "WARN $1"
  warn_count=$((warn_count + 1))
}

mark_pass() {
  echo "PASS $1"
}

echo "Sherlockdogs preflight"

SYSTEM_PYTHON="${PYTHON_BIN:-$(command -v python3 || true)}"
if [[ -n "$SYSTEM_PYTHON" && -x "$SYSTEM_PYTHON" ]]; then
  mark_pass "python=$SYSTEM_PYTHON"
else
  mark_fail "Python 3 not found. Install Python 3, then run Sherlockdogs Start again."
fi

if mkdir -p "$CONFIG_DIR" "$INBOX_DIR" >/dev/null 2>&1; then
  if touch "$CONFIG_DIR/.write-test" "$INBOX_DIR/.write-test" >/dev/null 2>&1; then
    rm -f "$CONFIG_DIR/.write-test" "$INBOX_DIR/.write-test"
    mark_pass "writable config/inbox"
  else
    mark_fail "Cannot write to $CONFIG_DIR or $INBOX_DIR."
  fi
else
  mark_fail "Cannot create $CONFIG_DIR or $INBOX_DIR."
fi

if [[ -x "$CODEX_BIN" ]] || command -v codex >/dev/null 2>&1; then
  mark_pass "codex available"
else
  mark_warn "Codex not found. Install/open Codex before expecting AI chatbox tasks."
fi

if command -v curl >/dev/null 2>&1; then
  if curl -fsI --max-time 5 https://pypi.org/simple/pip/ >/dev/null 2>&1; then
    mark_pass "network pypi.org reachable"
  else
    mark_warn "pypi.org not reachable. Dependency install may fail on this network."
  fi
else
  mark_warn "curl not found; skipping dependency network check."
fi

if command -v ffprobe >/dev/null 2>&1; then
  mark_pass "ffprobe available"
else
  mark_warn "ffprobe missing. Video duration/metadata may be limited until ffmpeg is installed."
fi

echo "summary fails=$fail_count warnings=$warn_count"
if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi
exit 0
