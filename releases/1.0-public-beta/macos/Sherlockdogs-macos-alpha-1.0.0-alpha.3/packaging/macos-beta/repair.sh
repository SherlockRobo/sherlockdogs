#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG_FILE="$HOME/.sherlockdogs/config.env"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Sherlockdogs config not found. Run Sherlockdogs Start first, then run Repair again." >&2
  exit 1
fi
set -a
source "$CONFIG_FILE"
set +a

SHERLOCKDOGS_PROJECT_DIR="${SHERLOCKDOGS_PROJECT_DIR:-$PROJECT_DIR}"
SHERLOCKDOGS_VENV_DIR="${SHERLOCKDOGS_VENV_DIR:-$HOME/.sherlockdogs/venv}"
PYTHON_BIN="${PYTHON_BIN:-$SHERLOCKDOGS_VENV_DIR/bin/python}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
LAUNCHD_PATH="$SHERLOCKDOGS_VENV_DIR/bin:/Applications/Codex.app/Contents/Resources:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
UID_VALUE="$(id -u)"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3 || true)"
fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
  echo "Python runtime not found. Run Sherlockdogs Start first." >&2
  exit 1
fi

mkdir -p "$SHERLOCKDOGS_PROJECT_DIR/jobs" "$SHERLOCKDOGS_PROJECT_DIR/runs" "$HOME/Library/LaunchAgents"

reload_plist() {
  local label="$1"
  local plist="$2"
  if [[ ! -f "$plist" ]]; then
    echo "skip=$label reason=plist_missing"
    return 0
  fi
  launchctl bootout "gui/$UID_VALUE" "$plist" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$UID_VALUE" "$plist"
  launchctl enable "gui/$UID_VALUE/$label" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$UID_VALUE/$label" >/dev/null 2>&1 || true
  echo "reloaded=$label"
}

ensure_codex_runner_plist() {
  local plist="$HOME/Library/LaunchAgents/com.sherlockdogs.codex-runner.plist"
  local clipping_dir="${SHERLOCKDOGS_CLIPPING_DIR:-${SHERLOCKDOGS_VAULT_DIR:-$HOME/ObsidianVault_LOCAL}/clipping}"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.sherlockdogs.codex-runner</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>set -a; source "$CONFIG_FILE"; set +a; export CODEX_BIN; export PYTHONDONTWRITEBYTECODE; export PATH="$LAUNCHD_PATH"; exec "$PYTHON_BIN" "$SHERLOCKDOGS_PROJECT_DIR/scripts/codex_runner.py" --limit 1 --codex-bin "$CODEX_BIN" --cwd "$clipping_dir"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$SHERLOCKDOGS_PROJECT_DIR/runs/codex-runner.launchd.out.log</string>
  <key>StandardErrorPath</key><string>$SHERLOCKDOGS_PROJECT_DIR/runs/codex-runner.launchd.err.log</string>
</dict></plist>
EOF
}

ensure_wechat_plist() {
  local plist="$HOME/Library/LaunchAgents/com.sherlockdogs.wechat-self.plist"
  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.sherlockdogs.wechat-self</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>set -a; source "$CONFIG_FILE"; set +a; export PYTHONDONTWRITEBYTECODE; export PATH="$LAUNCHD_PATH"; exec "$PYTHON_BIN" "$SHERLOCKDOGS_PROJECT_DIR/scripts/personal_wechat_inbox.py" --poll-timeout 300</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$SHERLOCKDOGS_PROJECT_DIR/runs/personal-wechat-inbox.out.log</string>
  <key>StandardErrorPath</key><string>$SHERLOCKDOGS_PROJECT_DIR/runs/personal-wechat-inbox.err.log</string>
</dict></plist>
EOF
}

echo "Sherlockdogs Repair"
echo "project=$SHERLOCKDOGS_PROJECT_DIR"
receiver_file="$SHERLOCKDOGS_PROJECT_DIR/jobs/personal_receiver_chats.txt"

if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/scripts/wechat_doctor.py" ]]; then
  echo "repair_wechat_binding=checking"
  if "$PYTHON_BIN" "$SHERLOCKDOGS_PROJECT_DIR/scripts/wechat_doctor.py" --lookback-seconds 86400 --show 10 --bind-latest >/tmp/sherlockdogs-repair-wechat.log 2>&1; then
    echo "repair_wechat_binding=ok"
  else
    echo "repair_wechat_binding=needs_connect_wechat"
    tail -20 /tmp/sherlockdogs-repair-wechat.log || true
  fi
fi

ensure_codex_runner_plist
reload_plist "com.sherlockdogs.codex-runner" "$HOME/Library/LaunchAgents/com.sherlockdogs.codex-runner.plist"

if [[ -f "$SHERLOCKDOGS_PROJECT_DIR/scripts/personal_wechat_inbox.py" ]]; then
  ensure_wechat_plist
  reload_plist "com.sherlockdogs.wechat-self" "$HOME/Library/LaunchAgents/com.sherlockdogs.wechat-self.plist"
  receiver_values=""
  if [[ -f "$receiver_file" ]]; then
    receiver_values="$(grep -v '^[[:space:]]*#' "$receiver_file" | awk 'NF {print $1}' | sort -u | paste -sd, -)"
  fi
  if [[ -z "$receiver_values" || "$receiver_values" == "filehelper" ]]; then
    echo "repair_wechat_scan=skipped reason=receiver_not_bound"
    echo "Forward one fresh item to your own WeChat account, then run Sherlockdogs Connect WeChat or Sherlockdogs Repair again."
  else
    echo "repair_wechat_scan=running_once receivers=$receiver_values"
    "$PYTHON_BIN" "$SHERLOCKDOGS_PROJECT_DIR/scripts/personal_wechat_inbox.py" --once --limit 80 --settle-seconds 0 --poll-timeout 180 || true
  fi
fi

launchctl kickstart -k "gui/$UID_VALUE/com.sherlockdogs.codex-runner" >/dev/null 2>&1 || true

if [[ -f "$PROJECT_DIR/packaging/macos-beta/doctor.sh" ]]; then
  bash "$PROJECT_DIR/packaging/macos-beta/doctor.sh" --report
fi

echo
echo "Repair finished."
echo "If WeChat still does not arrive, forward one fresh item to yourself, then run Sherlockdogs Repair again or Sherlockdogs Connect WeChat."
