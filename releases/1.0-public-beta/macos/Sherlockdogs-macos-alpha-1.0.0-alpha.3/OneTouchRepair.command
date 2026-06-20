#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/packaging/macos-beta"
./repair.sh
printf '
OneTouchRepair finished. Press Enter to close. '
read -r _
