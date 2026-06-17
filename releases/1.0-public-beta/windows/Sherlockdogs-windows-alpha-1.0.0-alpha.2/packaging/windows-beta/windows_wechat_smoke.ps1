param(
  [int]$TimeoutMinutes = 8,
  [string]$Receivers = "filehelper"
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
$ConnectScript = Join-Path $PSScriptRoot "connect_wechat.ps1"
$EvidenceScript = Join-Path $ProjectDir "scripts\collect_windows_wechat_db_evidence.py"

Write-Host "Sherlockdogs Windows WeChat smoke"
Write-Host "1. Keep Windows WeChat logged in."
Write-Host "2. This will connect the local WeChat DB watcher."
Write-Host "3. Then send a real '#2' item from phone WeChat to yourself."

& $ConnectScript -Receivers $Receivers
if ($LASTEXITCODE -ne 0) { throw "Connect WeChat failed." }
if (Test-Path $ConfigFile) { . $ConfigFile }

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first." }
if (-not (Test-Path $EvidenceScript)) { throw "Evidence script missing: $EvidenceScript" }

Write-Host ""
Write-Host "Now use phone WeChat to forward one test item to yourself."
Write-Host "Put #2 on its own line, or append #2 to the shared text."
Write-Host "Wait until Windows WeChat shows the message, then press Enter here."
Read-Host "Press Enter after Windows WeChat receives the #2 message"

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$LastOutput = ""
while ((Get-Date) -lt $Deadline) {
  $Output = & $Python $EvidenceScript --project-dir $ProjectDir --write 2>&1
  $LastOutput = ($Output | Out-String)
  Write-Host $LastOutput
  if ($LASTEXITCODE -eq 0) {
    Write-Host "Windows WeChat DB smoke PASS."
    exit 0
  }
  Write-Host "Evidence not ready yet; waiting 10 seconds..."
  Start-Sleep -Seconds 10
}

Write-Host $LastOutput
throw "Windows WeChat DB smoke did not pass within $TimeoutMinutes minutes. Run Doctor Sherlockdogs.cmd and send the latest diagnostics."
