#!/usr/bin/env bash
set -euo pipefail

LOCAL_PLIST="$HOME/Library/LaunchAgents/com.sherlockdogs.local-inbox.plist"
RUNNER_PLIST="$HOME/Library/LaunchAgents/com.sherlockdogs.codex-runner.plist"

launchctl bootout "gui/$(id -u)" "$LOCAL_PLIST" >/dev/null 2>&1 || true
launchctl bootout "gui/$(id -u)" "$RUNNER_PLIST" >/dev/null 2>&1 || true
rm -f "$LOCAL_PLIST" "$RUNNER_PLIST"

echo "Sherlockdogs LaunchAgents removed. User data and ~/.sherlockdogs/config.env were kept."
