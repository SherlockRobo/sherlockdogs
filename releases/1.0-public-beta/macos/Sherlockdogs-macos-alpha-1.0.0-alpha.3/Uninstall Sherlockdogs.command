#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/packaging/macos-beta"
./uninstall.sh
printf '
Uninstalled LaunchAgents. Press Enter to close. '
read -r _
