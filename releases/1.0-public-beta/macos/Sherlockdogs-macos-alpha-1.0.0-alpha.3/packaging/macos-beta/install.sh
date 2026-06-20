#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
NO_LOAD=0
SKIP_DEPS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-load) NO_LOAD=1 ;;
    --skip-deps) SKIP_DEPS=1 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

CONFIG_DIR="$HOME/.sherlockdogs"
CONFIG_FILE="$CONFIG_DIR/config.env"
INBOX_DIR="${SHERLOCKDOGS_INBOX_DIR:-$HOME/Sherlockdogs/Inbox}"
VENV_DIR="${SHERLOCKDOGS_VENV_DIR:-$CONFIG_DIR/venv}"

if [[ -n "${SHERLOCKDOGS_VAULT_DIR:-}" ]]; then
  VAULT_DIR="$SHERLOCKDOGS_VAULT_DIR"
elif [[ -d "$HOME/ObsidianVault_LOCAL" ]]; then
  VAULT_DIR="$HOME/ObsidianVault_LOCAL"
else
  VAULT_DIR="$HOME/Sherlockdogs/Vault"
fi

CLIPPING_DIR="${SHERLOCKDOGS_CLIPPING_DIR:-$VAULT_DIR/clipping}"
SYSTEM_PYTHON="${PYTHON_BIN:-$(command -v python3 || true)}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
LAUNCHD_PATH="$VENV_DIR/bin:/Applications/Codex.app/Contents/Resources:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

if [[ -z "$SYSTEM_PYTHON" ]]; then
  echo "Python 3 not found. Install Python 3 first." >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR" "$INBOX_DIR" "$CLIPPING_DIR"   "$PROJECT_DIR/jobs/pending" "$PROJECT_DIR/jobs/running"   "$PROJECT_DIR/jobs/done" "$PROJECT_DIR/jobs/failed" "$PROJECT_DIR/runs"   "$HOME/Library/LaunchAgents"

if [[ "$SKIP_DEPS" == "0" ]]; then
  "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -r "$PROJECT_DIR/packaging/macos-beta/requirements.txt"
  PYTHON_BIN="$VENV_DIR/bin/python"
else
  PYTHON_BIN="$SYSTEM_PYTHON"
fi

cat > "$CONFIG_FILE" <<EOF
SHERLOCKDOGS_PROJECT_DIR="$PROJECT_DIR"
SHERLOCKDOGS_INBOX_DIR="$INBOX_DIR"
SHERLOCKDOGS_VAULT_DIR="$VAULT_DIR"
SHERLOCKDOGS_CLIPPING_DIR="$CLIPPING_DIR"
SHERLOCKDOGS_VENV_DIR="$VENV_DIR"
PYTHON_BIN="$PYTHON_BIN"
CODEX_BIN="$CODEX_BIN"
PYTHONDONTWRITEBYTECODE="1"
EOF

LOCAL_PLIST="$HOME/Library/LaunchAgents/com.sherlockdogs.local-inbox.plist"
RUNNER_PLIST="$HOME/Library/LaunchAgents/com.sherlockdogs.codex-runner.plist"

cat > "$LOCAL_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.sherlockdogs.local-inbox</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>set -a; source "$CONFIG_FILE"; set +a; export PYTHONDONTWRITEBYTECODE; export PATH="$LAUNCHD_PATH"; exec "$PYTHON_BIN" "$PROJECT_DIR/scripts/local_inbox.py" --inbox-dir "$INBOX_DIR"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PROJECT_DIR/runs/local-inbox.launchd.out.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/runs/local-inbox.launchd.err.log</string>
</dict></plist>
EOF

cat > "$RUNNER_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.sherlockdogs.codex-runner</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>set -a; source "$CONFIG_FILE"; set +a; export CODEX_BIN; export PYTHONDONTWRITEBYTECODE; export PATH="$LAUNCHD_PATH"; exec "$PYTHON_BIN" "$PROJECT_DIR/scripts/codex_runner.py" --limit 1 --codex-bin "$CODEX_BIN" --cwd "$CLIPPING_DIR"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$PROJECT_DIR/runs/codex-runner.launchd.out.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/runs/codex-runner.launchd.err.log</string>
</dict></plist>
EOF

if [[ "$NO_LOAD" == "0" ]]; then
  launchctl bootout "gui/$(id -u)" "$LOCAL_PLIST" >/dev/null 2>&1 || true
  launchctl bootout "gui/$(id -u)" "$RUNNER_PLIST" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$LOCAL_PLIST"
  launchctl bootstrap "gui/$(id -u)" "$RUNNER_PLIST"
  launchctl enable "gui/$(id -u)/com.sherlockdogs.local-inbox" >/dev/null 2>&1 || true
  launchctl enable "gui/$(id -u)/com.sherlockdogs.codex-runner" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$(id -u)/com.sherlockdogs.local-inbox" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$(id -u)/com.sherlockdogs.codex-runner" >/dev/null 2>&1 || true
fi

echo "Sherlockdogs Mac alpha installed."
echo "Inbox: $INBOX_DIR"
echo "Clipping: $CLIPPING_DIR"
echo "Python: $PYTHON_BIN"
echo "Config: $CONFIG_FILE"
echo "Run doctor: $PROJECT_DIR/packaging/macos-beta/doctor.sh"
echo "Optional WeChat Personal Mode: $PROJECT_DIR/packaging/macos-beta/connect_wechat.sh"
if [[ "$NO_LOAD" == "1" ]]; then
  echo "LaunchAgents generated but not loaded (--no-load)."
fi
if [[ "$SKIP_DEPS" == "1" ]]; then
  echo "Dependency install skipped (--skip-deps)."
fi
