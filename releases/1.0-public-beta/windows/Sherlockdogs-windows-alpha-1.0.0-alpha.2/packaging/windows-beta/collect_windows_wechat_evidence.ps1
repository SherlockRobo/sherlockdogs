param(
  [switch]$NoDiscoverReceiver,
  [string]$RequireToken = "",
  [string]$OutDir = ""
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
$InboxScript = Join-Path $ProjectDir "scripts\windows_wechat_inbox.py"
$EvidenceScript = Join-Path $ProjectDir "scripts\collect_windows_wechat_db_evidence.py"

if (-not (Test-Path $ConfigFile)) { throw "Sherlockdogs config missing. Run Sherlockdogs Start.cmd, then Sherlockdogs Connect WeChat.cmd." }
. $ConfigFile

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first." }
if (-not (Test-Path $InboxScript)) { throw "Windows WeChat inbox script missing: $InboxScript" }
if (-not (Test-Path $EvidenceScript)) { throw "Evidence script missing: $EvidenceScript" }

$DbRoot = $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR
if (-not $DbRoot -or -not (Test-Path $DbRoot)) {
  throw "Windows WeChat DB root missing. Run Sherlockdogs Connect WeChat.cmd with Windows WeChat logged in."
}

$ReceiverArg = if ($NoDiscoverReceiver) { "" } else { "*" }
$AdapterArgs = @($InboxScript, "--once", "--db-root", $DbRoot, "--settle-seconds", "0")
if ($ReceiverArg) { $AdapterArgs += @("--receivers", $ReceiverArg) }

$AdapterOutput = & $Python @AdapterArgs 2>&1
$AdapterText = ($AdapterOutput | Out-String)
Write-Host $AdapterText
if ($LASTEXITCODE -ne 0) { throw "Windows WeChat adapter failed before evidence collection." }

$EvidenceArgs = @($EvidenceScript, "--project-dir", $ProjectDir, "--write")
if ($RequireToken) { $EvidenceArgs += @("--require-token", $RequireToken) }
if ($OutDir) { $EvidenceArgs += @("--out-dir", $OutDir) }
$EvidenceOutput = & $Python @EvidenceArgs 2>&1
$EvidenceText = ($EvidenceOutput | Out-String)
Write-Host $EvidenceText
if ($LASTEXITCODE -ne 0) { throw "Windows WeChat DB smoke evidence is not ready yet." }

$ReceiverLine = ($EvidenceOutput | Where-Object { $_ -match '^receiver_chat=' } | Select-Object -First 1)
if ($ReceiverLine) {
  $ReceiverChat = ($ReceiverLine -replace '^receiver_chat=', '').Trim()
  if ($ReceiverChat -and -not $NoDiscoverReceiver) {
    $ReceiverFile = Join-Path $ProjectDir "jobs\windows_receiver_chats.txt"
    $ReceiverChat | Set-Content -Encoding UTF8 $ReceiverFile
    Write-Host "Discovered Windows WeChat receiver_chat=$ReceiverChat"
    Write-Host "Saved receiver config: $ReceiverFile"
  }
}

Write-Host "Windows WeChat DB smoke evidence PASS."
