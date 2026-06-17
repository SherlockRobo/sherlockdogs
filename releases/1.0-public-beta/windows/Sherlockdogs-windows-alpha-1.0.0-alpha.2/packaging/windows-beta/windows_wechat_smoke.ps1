param(
  [int]$TimeoutMinutes = 8,
  [string]$Receivers = "*"
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
$InstallScript = Join-Path $PSScriptRoot "install.ps1"
$ConnectScript = Join-Path $PSScriptRoot "connect_wechat.ps1"
$CollectScript = Join-Path $PSScriptRoot "collect_windows_wechat_evidence.ps1"
$DoctorScript = Join-Path $PSScriptRoot "doctor.ps1"
$ExportScript = Join-Path $PSScriptRoot "export_windows_evidence.ps1"

function Export-Evidence {
  if (-not (Test-Path $ExportScript)) { return }
  try {
    & $ExportScript -SkipDoctor
  } catch {
    Write-Host "Evidence export failed: $($_.Exception.Message)"
  }
}

Write-Host "Sherlockdogs Windows WeChat smoke"
Write-Host "1. Keep Windows WeChat logged in."
Write-Host "2. This will make sure Sherlockdogs is installed, then connect the local WeChat DB watcher."
Write-Host "3. Then send the generated '#2' smoke text from phone WeChat to yourself."

if (-not (Test-Path $ConfigFile)) {
  if (-not (Test-Path $InstallScript)) { throw "Install script missing: $InstallScript" }
  Write-Host "Sherlockdogs config missing; running install first."
  & $InstallScript
  if ($LASTEXITCODE -ne 0) { throw "Install Sherlockdogs failed." }
}

& $ConnectScript -Receivers $Receivers
if ($LASTEXITCODE -ne 0) { throw "Connect WeChat failed." }
if (Test-Path $ConfigFile) { . $ConfigFile }

if (-not (Test-Path $CollectScript)) { throw "Evidence collector missing: $CollectScript" }

$SmokeToken = "sdogs-win-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + ([System.Guid]::NewGuid().ToString("N").Substring(0, 8))
$SmokeText = @"
https://example.com/sherlockdogs-windows-smoke
#2
$SmokeToken
"@

Write-Host ""
Write-Host "Now use phone WeChat to send this exact smoke text to yourself:"
Write-Host "----- Sherlockdogs smoke text -----"
Write-Host $SmokeText
Write-Host "----- end -----"
Write-Host "Wait until Windows WeChat shows this exact token, then press Enter here."
Read-Host "Press Enter after Windows WeChat receives token $SmokeToken"

$Deadline = (Get-Date).AddMinutes($TimeoutMinutes)
$LastOutput = ""
while ((Get-Date) -lt $Deadline) {
  $CollectExit = 1
  try {
    $Output = & $CollectScript -RequireToken $SmokeToken 2>&1
    $CollectExit = $LASTEXITCODE
  } catch {
    $Output = @($_.Exception.Message)
    $CollectExit = 1
  }
  $LastOutput = ($Output | Out-String)
  Write-Host $LastOutput
  if ($CollectExit -eq 0) {
    Write-Host "Windows WeChat DB smoke PASS."
    Export-Evidence
    exit 0
  }
  Write-Host "Evidence not ready yet; waiting 10 seconds..."
  Start-Sleep -Seconds 10
}

Write-Host $LastOutput
if (Test-Path $DoctorScript) {
  Write-Host "Collecting Doctor report after timeout..."
  try {
    & $DoctorScript -Report
  } catch {
    Write-Host "Doctor report failed: $($_.Exception.Message)"
  }
}
Export-Evidence
throw "Windows WeChat DB smoke did not pass within $TimeoutMinutes minutes. Run Doctor Sherlockdogs.cmd and send the latest diagnostics."
