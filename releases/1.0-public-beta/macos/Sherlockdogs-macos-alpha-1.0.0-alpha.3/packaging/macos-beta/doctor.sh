#!/usr/bin/env bash
set -euo pipefail

WRITE_REPORT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --report) WRITE_REPORT=1 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG_FILE="$HOME/.sherlockdogs/config.env"
if [[ -f "$CONFIG_FILE" ]]; then
  set -a
  source "$CONFIG_FILE"
  set +a
fi

SHERLOCKDOGS_PROJECT_DIR="${SHERLOCKDOGS_PROJECT_DIR:-$PROJECT_DIR}"
SHERLOCKDOGS_INBOX_DIR="${SHERLOCKDOGS_INBOX_DIR:-$HOME/Sherlockdogs/Inbox}"
SHERLOCKDOGS_VAULT_DIR="${SHERLOCKDOGS_VAULT_DIR:-$HOME/ObsidianVault_LOCAL}"
SHERLOCKDOGS_CLIPPING_DIR="${SHERLOCKDOGS_CLIPPING_DIR:-$SHERLOCKDOGS_VAULT_DIR/clipping}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
SHERLOCKDOGS_VENV_DIR="${SHERLOCKDOGS_VENV_DIR:-$HOME/.sherlockdogs/venv}"
MANIFEST_PATH="$PROJECT_DIR/packaging/macos-beta/manifest.json"

ok_path() { [[ -e "$1" ]] && echo "ok" || echo "missing"; }
ok_exec() { [[ -x "$1" ]] && echo "ok" || echo "missing"; }
count_dir() {
  local dir="$1"
  if [[ -d "$dir" ]]; then
    find "$dir" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' '
  else
    echo 0
  fi
}
status_label() {
  local label="$1"
  if launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1; then
    echo "running"
  else
    echo "not loaded"
  fi
}
enabled_label() {
  local label="$1"
  local line
  line="$(launchctl print-disabled "gui/$(id -u)" 2>/dev/null | rg "\"$label\"" || true)"
  if [[ "$line" == *"=> disabled"* ]]; then
    echo "disabled"
  elif [[ "$line" == *"=> enabled"* ]]; then
    echo "enabled"
  else
    echo "default"
  fi
}
module_status() {
  local module="$1"
  if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "missing-python"
    return
  fi
  if "$PYTHON_BIN" -c "import $module" >/dev/null 2>&1; then
    echo "ok"
  else
    echo "missing"
  fi
}
bin_status() {
  local bin="$1"
  if [[ -x "$SHERLOCKDOGS_VENV_DIR/bin/$bin" ]]; then
    echo "ok-venv"
  elif command -v "$bin" >/dev/null 2>&1; then
    echo "ok"
  else
    echo "missing"
  fi
}
manifest_value() {
  local key="$1"
  if [[ -f "$MANIFEST_PATH" && -n "$PYTHON_BIN" && -x "$PYTHON_BIN" ]]; then
    "$PYTHON_BIN" -c "import json; from pathlib import Path; print(json.loads(Path('$MANIFEST_PATH').read_text()).get('$key', ''))" 2>/dev/null || true
  fi
}

emit_report() {
  echo "Sherlockdogs doctor"
  echo "version=$(manifest_value version)"
  echo "channel=$(manifest_value channel)"
  echo "project=$SHERLOCKDOGS_PROJECT_DIR status=$(ok_path "$SHERLOCKDOGS_PROJECT_DIR")"
  echo "manifest=$MANIFEST_PATH status=$(ok_path "$MANIFEST_PATH")"
  echo "config=$CONFIG_FILE status=$(ok_path "$CONFIG_FILE")"
  echo "inbox=$SHERLOCKDOGS_INBOX_DIR status=$(ok_path "$SHERLOCKDOGS_INBOX_DIR")"
  echo "vault=$SHERLOCKDOGS_VAULT_DIR status=$(ok_path "$SHERLOCKDOGS_VAULT_DIR")"
  echo "clipping=$SHERLOCKDOGS_CLIPPING_DIR status=$(ok_path "$SHERLOCKDOGS_CLIPPING_DIR")"
  echo "python=$PYTHON_BIN status=$(ok_exec "$PYTHON_BIN")"
  echo "venv=$SHERLOCKDOGS_VENV_DIR status=$(ok_path "$SHERLOCKDOGS_VENV_DIR")"
  echo "codex=$CODEX_BIN status=$(ok_exec "$CODEX_BIN")"
  echo "module.requests=$(module_status requests)"
  echo "module.bs4=$(module_status bs4)"
  echo "module.markdownify=$(module_status markdownify)"
  echo "module.PIL=$(module_status PIL)"
  echo "binary.yt-dlp=$(bin_status yt-dlp)"
  echo "binary.ffprobe=$(bin_status ffprobe)"
  echo "local-inbox=$(status_label com.sherlockdogs.local-inbox)"
  echo "local-inbox-enabled=$(enabled_label com.sherlockdogs.local-inbox)"
  echo "wechat-self=$(status_label com.sherlockdogs.wechat-self)"
  echo "wechat-self-enabled=$(enabled_label com.sherlockdogs.wechat-self)"
  echo "codex-runner=$(status_label com.sherlockdogs.codex-runner)"
  echo "codex-runner-enabled=$(enabled_label com.sherlockdogs.codex-runner)"
  echo "pending=$(count_dir "$SHERLOCKDOGS_PROJECT_DIR/jobs/pending")"
  echo "running=$(count_dir "$SHERLOCKDOGS_PROJECT_DIR/jobs/running")"
  echo "done=$(count_dir "$SHERLOCKDOGS_PROJECT_DIR/jobs/done")"
  echo "failed=$(count_dir "$SHERLOCKDOGS_PROJECT_DIR/jobs/failed")"

  echo "next_steps:"
  local advice_count=0
  if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "- Install Python 3, then run Install Sherlockdogs.command again."
    advice_count=$((advice_count + 1))
  fi
  if [[ ! -x "$CODEX_BIN" ]]; then
    echo "- Install/open Codex, or set CODEX_BIN in $CONFIG_FILE."
    advice_count=$((advice_count + 1))
  fi
  if [[ "$(module_status requests)" != "ok" || "$(module_status bs4)" != "ok" || "$(module_status markdownify)" != "ok" || "$(module_status PIL)" != "ok" ]]; then
    echo "- Run Install Sherlockdogs.command again to rebuild Python dependencies."
    advice_count=$((advice_count + 1))
  fi
  if [[ "$(bin_status ffprobe)" == "missing" ]]; then
    echo "- Video metadata may be limited until ffprobe/ffmpeg is installed."
    advice_count=$((advice_count + 1))
  fi
  if [[ "$(status_label com.sherlockdogs.local-inbox)" != "running" || "$(status_label com.sherlockdogs.codex-runner)" != "running" ]]; then
    echo "- Background services are not both running; run Sherlockdogs Repair.app or Sherlockdogs Start.app again."
    advice_count=$((advice_count + 1))
  fi
  if [[ "$(enabled_label com.sherlockdogs.local-inbox)" == "disabled" || "$(enabled_label com.sherlockdogs.codex-runner)" == "disabled" || "$(enabled_label com.sherlockdogs.wechat-self)" == "disabled" ]]; then
    echo "- Some background services are disabled; run Sherlockdogs Repair.app."
    advice_count=$((advice_count + 1))
  fi
  if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/scripts/wechat_doctor.py" ]]; then
    echo "- Optional: to use WeChat Personal Mode, run Sherlockdogs Connect WeChat after forwarding a test message to yourself."
  fi
  if [[ "$(count_dir "$SHERLOCKDOGS_PROJECT_DIR/jobs/failed")" != "0" ]]; then
    echo "- Failed jobs exist; open Diagnostics and send the latest doctor report."
    advice_count=$((advice_count + 1))
  fi
  if [[ "$advice_count" == "0" ]]; then
    echo "- OK: drop files or links into $SHERLOCKDOGS_INBOX_DIR."
    echo "- Results will appear under $SHERLOCKDOGS_CLIPPING_DIR."
  fi

  if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/runs/local-inbox.launchd.err.log" ]]; then
    echo "local-inbox recent errors:"
    tail -n 5 "$SHERLOCKDOGS_PROJECT_DIR/runs/local-inbox.launchd.err.log" || true
  fi
  if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/runs/codex-runner.launchd.err.log" ]]; then
    echo "codex-runner recent errors:"
    tail -n 5 "$SHERLOCKDOGS_PROJECT_DIR/runs/codex-runner.launchd.err.log" || true
  fi
  if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/runs/personal-wechat-inbox.err.log" ]]; then
    echo "wechat-self recent errors:"
    tail -n 5 "$SHERLOCKDOGS_PROJECT_DIR/runs/personal-wechat-inbox.err.log" || true
  fi
}

if [[ "$WRITE_REPORT" == "1" ]]; then
  report_dir="$HOME/.sherlockdogs/diagnostics"
  mkdir -p "$report_dir"
  report_path="$report_dir/doctor-$(date +%Y%m%d-%H%M%S).txt"
  emit_report | tee "$report_path"
  echo "diagnostic_report=$report_path"
else
  emit_report
fi
