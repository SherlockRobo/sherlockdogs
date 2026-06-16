#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG_FILE="$HOME/.sherlockdogs/config.env"
if [[ -f "$CONFIG_FILE" ]]; then
  set -a
  source "$CONFIG_FILE"
  set +a
fi

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
  echo "Python runtime not found. Run Sherlockdogs Start first." >&2
  exit 1
fi

mkdir -p "$PROJECT_DIR/jobs" "$PROJECT_DIR/runs" "$HOME/Library/LaunchAgents"

echo "Sherlockdogs WeChat Personal Mode"
echo
echo "请确认："
echo "1. Mac 微信已经登录。"
echo "2. 手机微信刚刚把一条文章/链接/图片转发给你自己。"
echo
echo "正在检查最近微信消息并自动绑定接收会话..."

"$PYTHON_BIN" "$PROJECT_DIR/scripts/wechat_doctor.py" --lookback-seconds 3600 --show 5 --bind-latest --require-bind

WECHAT_PLIST="$HOME/Library/LaunchAgents/com.sherlockdogs.wechat-self.plist"
cat > "$WECHAT_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.sherlockdogs.wechat-self</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>-lc</string>
    <string>set -a; source "$CONFIG_FILE"; set +a; export PYTHONDONTWRITEBYTECODE; export PATH="\${SHERLOCKDOGS_VENV_DIR:-$HOME/.sherlockdogs/venv}/bin:/Applications/Codex.app/Contents/Resources:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"; exec "$PYTHON_BIN" "$PROJECT_DIR/scripts/personal_wechat_inbox.py"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$PROJECT_DIR/runs/personal-wechat-inbox.out.log</string>
  <key>StandardErrorPath</key><string>$PROJECT_DIR/runs/personal-wechat-inbox.err.log</string>
</dict></plist>
EOF

launchctl bootout "gui/$(id -u)" "$WECHAT_PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$WECHAT_PLIST"
launchctl kickstart -k "gui/$(id -u)/com.sherlockdogs.wechat-self" >/dev/null 2>&1 || true

echo
echo "WeChat Personal Mode enabled."
echo "以后手机把内容转发给自己的微信，Mac 收到后会自动进入 Sherlockdogs。"
echo "Receiver file: $PROJECT_DIR/jobs/personal_receiver_chats.txt"
