#!/usr/bin/env bash
set -euo pipefail
CONFIG_FILE="$HOME/.sherlockdogs/config.env"
if [[ -f "$CONFIG_FILE" ]]; then
  set -a
  source "$CONFIG_FILE"
  set +a
fi
OUTPUT_DIR="${SHERLOCKDOGS_CLIPPING_DIR:-$HOME/ObsidianVault_LOCAL/clipping}"
if [[ ! -d "$(dirname "$OUTPUT_DIR")" && "$OUTPUT_DIR" == "$HOME/ObsidianVault_LOCAL/clipping" ]]; then
  OUTPUT_DIR="$HOME/Sherlockdogs/Vault/clipping"
fi
mkdir -p "$OUTPUT_DIR"
open "$OUTPUT_DIR"
echo "Opened Output: $OUTPUT_DIR"
