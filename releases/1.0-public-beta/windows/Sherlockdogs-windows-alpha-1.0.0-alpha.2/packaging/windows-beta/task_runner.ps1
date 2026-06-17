param(
  [ValidateSet("local-inbox", "codex-runner", "windows-wechat")]
  [string]$Kind
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (-not (Test-Path $ConfigFile)) { throw "Sherlockdogs config missing: $ConfigFile" }
. $ConfigFile

$DiagnosticsDir = Join-Path $env:USERPROFILE ".sherlockdogs\diagnostics"
New-Item -ItemType Directory -Force -Path $DiagnosticsDir | Out-Null
$TaskLog = Join-Path $DiagnosticsDir ("task-{0}-{1}.log" -f $Kind, (Get-Date -Format yyyyMMdd-HHmmss))

function Add-TaskLog([string]$Line) {
  Add-Content -Encoding UTF8 -Path $TaskLog -Value $Line
}

function Invoke-LoggedPython([array]$ArgsList) {
  Add-TaskLog "command=$Python $($ArgsList -join ' ')"
  $Output = & $Python @ArgsList 2>&1
  $ExitCode = $LASTEXITCODE
  $Output | ForEach-Object { Add-TaskLog $_ }
  Add-TaskLog "exit_code=$ExitCode"
  Write-Host ($Output | Out-String)
  exit $ExitCode
}

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first." }
Add-TaskLog "Sherlockdogs task runner"
Add-TaskLog "started_at=$(Get-Date -Format o)"
Add-TaskLog "kind=$Kind"
Add-TaskLog "project=$ProjectDir"
Add-TaskLog "python=$Python"
Add-TaskLog "config=$ConfigFile"

if ($Kind -eq "local-inbox") {
  $InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
  Invoke-LoggedPython @((Join-Path $ProjectDir "scripts\local_inbox.py"), "--once", "--inbox-dir", $InboxDir)
}

if ($Kind -eq "codex-runner") {
  $Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { "codex" }
  $ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault\clipping" }
  Invoke-LoggedPython @((Join-Path $ProjectDir "scripts\codex_runner.py"), "--limit", "1", "--codex-bin", $Codex, "--cwd", $ClippingDir)
}

if ($Kind -eq "windows-wechat") {
  $DbRoot = $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR
  if (-not $DbRoot) { throw "SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR is not configured." }
  Invoke-LoggedPython @((Join-Path $ProjectDir "scripts\windows_wechat_inbox.py"), "--once", "--db-root", $DbRoot)
}

throw "Unknown task kind: $Kind"
