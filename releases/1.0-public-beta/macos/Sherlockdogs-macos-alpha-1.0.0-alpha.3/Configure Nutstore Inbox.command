#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/packaging/macos-beta"
./configure_nutstore_inbox.sh
printf '
Nutstore Inbox configured. Press Enter to close. '
read -r _
