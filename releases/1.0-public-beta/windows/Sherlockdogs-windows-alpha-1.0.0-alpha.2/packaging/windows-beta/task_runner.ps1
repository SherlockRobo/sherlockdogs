param(
  [ValidateSet("local-inbox", "codex-runner", "windows-wechat")]
  [string]$Kind
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (-not (Test-Path $ConfigFile)) { throw "Sherlockdogs config missing: $ConfigFile" }
. $ConfigFile

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first." }

if ($Kind -eq "local-inbox") {
  $InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
  & $Python (Join-Path $ProjectDir "scripts\local_inbox.py") --once --inbox-dir $InboxDir
  exit $LASTEXITCODE
}

if ($Kind -eq "codex-runner") {
  $Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { "codex" }
  $ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault\clipping" }
  & $Python (Join-Path $ProjectDir "scripts\codex_runner.py") --limit 1 --codex-bin $Codex --cwd $ClippingDir
  exit $LASTEXITCODE
}

if ($Kind -eq "windows-wechat") {
  $DbRoot = $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR
  if (-not $DbRoot) { throw "SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR is not configured." }
  & $Python (Join-Path $ProjectDir "scripts\windows_wechat_inbox.py") --once --db-root $DbRoot
  exit $LASTEXITCODE
}

throw "Unknown task kind: $Kind"
