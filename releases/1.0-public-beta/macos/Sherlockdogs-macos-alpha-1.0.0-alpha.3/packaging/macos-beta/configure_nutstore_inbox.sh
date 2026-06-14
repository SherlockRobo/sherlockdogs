#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG_DIR="$HOME/.sherlockdogs"
CONFIG_FILE="$CONFIG_DIR/config.env"
NO_LOAD=0
NUTSTORE_ROOT="${SHERLOCKDOGS_NUTSTORE_DIR:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --path) NUTSTORE_ROOT="${2:-}"; shift 2 ;;
    --no-load) NO_LOAD=1; shift ;;
    --help|-h)
      cat <<'USAGE'
Usage:
  Configure Nutstore Inbox.command
  SHERLOCKDOGS_NUTSTORE_DIR="$HOME/Nutstore Files" configure_nutstore_inbox.sh
  configure_nutstore_inbox.sh --path "$HOME/Nutstore Files"
  configure_nutstore_inbox.sh --path "$HOME/Library/Mobile Documents/com~apple~CloudDocs"
USAGE
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

detect_nutstore_root() {
  local candidates=(
    "$HOME/Library/CloudStorage/坚果云-"*/Nutstore
    "$HOME/Library/CloudStorage/Nutstore-"*/Nutstore
    "$HOME/Nutstore Files"
    "$HOME/坚果云"
    "$HOME/Nutstore"
    "$HOME/Documents/Nutstore Files"
    "$HOME/Documents/坚果云"
  )
  local path
  for path in "${candidates[@]}"; do
    if [[ -d "$path" ]]; then
      printf '%s\n' "$path"
      return 0
    fi
  done
  find "$HOME/Library/CloudStorage" "$HOME" -maxdepth 3 -type d \( -name 'Nutstore Files' -o -name '坚果云' -o -name 'Nutstore' \) 2>/dev/null | head -1
}

if [[ -z "$NUTSTORE_ROOT" ]]; then
  NUTSTORE_ROOT="$(detect_nutstore_root || true)"
fi

if [[ -z "$NUTSTORE_ROOT" ]]; then
  cat >&2 <<'EOF2'
Nutstore sync folder was not found.

Install and sign in to Nutstore first, then rerun this command.
If your Nutstore folder is custom, run:
  SHERLOCKDOGS_NUTSTORE_DIR="/path/to/Nutstore" Configure Nutstore Inbox.command
EOF2
  exit 1
fi

mkdir -p "$CONFIG_DIR"
NUTSTORE_ROOT="$(cd "$NUTSTORE_ROOT" && pwd)"
INBOX_DIR="$NUTSTORE_ROOT/Sherlockdogs/Inbox"
OUTBOX_DIR="$NUTSTORE_ROOT/Sherlockdogs/Outbox"
mkdir -p "$INBOX_DIR" "$OUTBOX_DIR"

# Preserve existing configuration when present.
SHERLOCKDOGS_PROJECT_DIR="$PROJECT_DIR"
SHERLOCKDOGS_VAULT_DIR="${SHERLOCKDOGS_VAULT_DIR:-}"
SHERLOCKDOGS_CLIPPING_DIR="${SHERLOCKDOGS_CLIPPING_DIR:-}"
SHERLOCKDOGS_VENV_DIR="${SHERLOCKDOGS_VENV_DIR:-$CONFIG_DIR/venv}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
CODEX_BIN="${CODEX_BIN:-/Applications/Codex.app/Contents/Resources/codex}"
if [[ -f "$CONFIG_FILE" ]]; then
  set -a
  source "$CONFIG_FILE"
  set +a
fi
if [[ -z "${SHERLOCKDOGS_VAULT_DIR:-}" ]]; then
  if [[ -d "$HOME/ObsidianVault_LOCAL" ]]; then
    SHERLOCKDOGS_VAULT_DIR="$HOME/ObsidianVault_LOCAL"
  else
    SHERLOCKDOGS_VAULT_DIR="$HOME/Sherlockdogs/Vault"
  fi
fi
if [[ -z "${SHERLOCKDOGS_CLIPPING_DIR:-}" ]]; then
  SHERLOCKDOGS_CLIPPING_DIR="$SHERLOCKDOGS_VAULT_DIR/clipping"
fi

cat > "$CONFIG_FILE" <<EOF2
SHERLOCKDOGS_PROJECT_DIR="$PROJECT_DIR"
SHERLOCKDOGS_INBOX_DIR="$INBOX_DIR"
SHERLOCKDOGS_NUTSTORE_DIR="$NUTSTORE_ROOT"
SHERLOCKDOGS_VAULT_DIR="$SHERLOCKDOGS_VAULT_DIR"
SHERLOCKDOGS_CLIPPING_DIR="$SHERLOCKDOGS_CLIPPING_DIR"
SHERLOCKDOGS_VENV_DIR="$SHERLOCKDOGS_VENV_DIR"
PYTHON_BIN="$PYTHON_BIN"
CODEX_BIN="$CODEX_BIN"
PYTHONDONTWRITEBYTECODE="1"
EOF2

if [[ -x "$PROJECT_DIR/packaging/macos-beta/install.sh" ]]; then
  if [[ "$NO_LOAD" == "1" ]]; then
    SHERLOCKDOGS_INBOX_DIR="$INBOX_DIR" "$PROJECT_DIR/packaging/macos-beta/install.sh" --skip-deps --no-load >/tmp/sdogs-nutstore-install.log
  else
    SHERLOCKDOGS_INBOX_DIR="$INBOX_DIR" "$PROJECT_DIR/packaging/macos-beta/install.sh" --skip-deps >/tmp/sdogs-nutstore-install.log
  fi
fi

open "$INBOX_DIR" >/dev/null 2>&1 || true
cat <<EOF2
Sherlockdogs Nutstore Inbox configured.
Nutstore: $NUTSTORE_ROOT
Inbox: $INBOX_DIR
Config: $CONFIG_FILE

Phone shortcut target folder:
  /Sherlockdogs/Inbox

Nutstore WebDAV base:
  https://dav.jianguoyun.com/dav/
EOF2
