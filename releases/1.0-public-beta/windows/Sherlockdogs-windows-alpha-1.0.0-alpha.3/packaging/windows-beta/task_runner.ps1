param(
  [ValidateSet("local-inbox", "codex-runner", "windows-wechat")]
  [string]$Kind
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

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

function Invoke-LoggedProcess([string]$Exe, [array]$ArgsList) {
  Add-TaskLog "command=$Exe $($ArgsList -join ' ')"
  $Output = & $Exe @ArgsList 2>&1
  $ExitCode = $LASTEXITCODE
  $Output | ForEach-Object { Add-TaskLog $_ }
  Add-TaskLog "exit_code=$ExitCode"
  Write-Host ($Output | Out-String)
  return $ExitCode
}

function Invoke-LoggedPython([array]$ArgsList) {
  $ExitCode = Invoke-LoggedProcess $Python $ArgsList
  exit $ExitCode
}

function Invoke-WeChatIncrementalDecrypt {
  $ToolRoot = Join-Path $env:USERPROFILE ".sherlockdogs\tools"
  $WeChatDecryptDir = Join-Path $ToolRoot "wechat-decrypt"
  $Candidates = @(
    @{ Name = "decrypt_db.py --incremental"; Script = (Join-Path $WeChatDecryptDir "decrypt_db.py"); Args = @("--incremental") },
    @{ Name = "decrypt.py --incremental"; Script = (Join-Path $WeChatDecryptDir "decrypt.py"); Args = @("--incremental") },
    @{ Name = "main.py decrypt --incremental"; Script = (Join-Path $WeChatDecryptDir "main.py"); Args = @("decrypt", "--incremental") },
    @{ Name = "main.py decrypt"; Script = (Join-Path $WeChatDecryptDir "main.py"); Args = @("decrypt") }
  )

  $Tried = 0
  foreach ($Candidate in $Candidates) {
    if (-not (Test-Path $Candidate.Script)) { continue }
    $Tried += 1
    Add-TaskLog "incremental_decrypt_try=$($Candidate.Name)"
    $ArgsList = @($Candidate.Script) + $Candidate.Args
    $ExitCode = Invoke-LoggedProcess $Python $ArgsList
    if ($ExitCode -eq 0) {
      Add-TaskLog "incremental_decrypt=ok"
      return
    }
    Add-TaskLog "incremental_decrypt_failed=$($Candidate.Name)"
  }

  if ($Tried -eq 0) {
    Add-TaskLog "incremental_decrypt=skipped reason=no_wechat_decrypt_helper"
    return
  }
  throw "Windows WeChat incremental decrypt failed. Run '3 OneClick Repair.cmd' or '4 OneClick Report.cmd'."
}

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw "Python not found. Run 1 OneClick Install.cmd first." }
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
  Invoke-WeChatIncrementalDecrypt
  Invoke-LoggedPython @((Join-Path $ProjectDir "scripts\windows_wechat_inbox.py"), "--once", "--db-root", $DbRoot)
}

throw "Unknown task kind: $Kind"
