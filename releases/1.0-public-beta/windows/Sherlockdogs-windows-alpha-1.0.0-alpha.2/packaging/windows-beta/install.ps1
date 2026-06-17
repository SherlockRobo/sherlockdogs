param(
  [switch]$NoTasks,
  [switch]$SkipDeps
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigDir = Join-Path $env:USERPROFILE ".sherlockdogs"
$ConfigFile = Join-Path $ConfigDir "config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }
$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$NutstoreDir = if ($env:SHERLOCKDOGS_NUTSTORE_DIR) { $env:SHERLOCKDOGS_NUTSTORE_DIR } else { "" }
$VaultDir = if ($env:SHERLOCKDOGS_VAULT_DIR) { $env:SHERLOCKDOGS_VAULT_DIR } elseif (Test-Path (Join-Path $env:USERPROFILE "ObsidianVault_LOCAL")) { Join-Path $env:USERPROFILE "ObsidianVault_LOCAL" } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault" }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $VaultDir "clipping" }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $ConfigDir "venv" }
$WindowsWeChatDir = if ($env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR) { $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR } else { "" }
$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }

if (-not $Python) { throw "Python not found. Install Python 3 and retry." }
if (-not $Codex) { $Codex = "codex" }

function Quote-PsString([string]$Value) {
  return "'" + (($Value -as [string]) -replace "'", "''") + "'"
}

New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir, $ClippingDir, (Join-Path $ProjectDir "jobs\pending"), (Join-Path $ProjectDir "jobs\running"), (Join-Path $ProjectDir "jobs\done"), (Join-Path $ProjectDir "jobs\failed"), (Join-Path $ProjectDir "runs") | Out-Null

if (-not $SkipDeps) {
  & $Python -m venv $VenvDir
  $PythonBin = Join-Path $VenvDir "Scripts\python.exe"
  & $PythonBin -m pip install --upgrade pip
  & $PythonBin -m pip install -r (Join-Path $ProjectDir "packaging\windows-beta\requirements.txt")
} else {
  $PythonBin = $Python
}

$ConfigLines = @(
  "`$env:SHERLOCKDOGS_PROJECT_DIR = $(Quote-PsString $ProjectDir)",
  "`$env:SHERLOCKDOGS_INBOX_DIR = $(Quote-PsString $InboxDir)",
  "`$env:SHERLOCKDOGS_VAULT_DIR = $(Quote-PsString $VaultDir)",
  "`$env:SHERLOCKDOGS_CLIPPING_DIR = $(Quote-PsString $ClippingDir)",
  "`$env:SHERLOCKDOGS_VENV_DIR = $(Quote-PsString $VenvDir)",
  "`$env:PYTHON_BIN = $(Quote-PsString $PythonBin)",
  "`$env:CODEX_BIN = $(Quote-PsString $Codex)",
  "`$env:PYTHONDONTWRITEBYTECODE = '1'",
  "`$env:PATH = (Join-Path $(Quote-PsString $VenvDir) 'Scripts') + ';' + `$env:PATH"
)
if ($NutstoreDir) { $ConfigLines += "`$env:SHERLOCKDOGS_NUTSTORE_DIR = $(Quote-PsString $NutstoreDir)" }
if ($WindowsWeChatDir) { $ConfigLines += "`$env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR = $(Quote-PsString $WindowsWeChatDir)" }
$ConfigLines | Set-Content -Encoding UTF8 $ConfigFile

if (-not $NoTasks) {
  $TaskRunner = Join-Path $ProjectDir "packaging\windows-beta\task_runner.ps1"
  $TaskSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
  $InboxAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$TaskRunner`" -Kind local-inbox"
  $InboxTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds 15) -RepetitionDuration (New-TimeSpan -Days 3650)
  Register-ScheduledTask -TaskName "SherlockdogsLocalInbox" -Action $InboxAction -Trigger $InboxTrigger -Settings $TaskSettings -Description "Sherlockdogs local Inbox watcher" -Force | Out-Null
  Start-ScheduledTask -TaskName "SherlockdogsLocalInbox" -ErrorAction SilentlyContinue

  $RunnerAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$TaskRunner`" -Kind codex-runner"
  $RunnerTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds 30) -RepetitionDuration (New-TimeSpan -Days 3650)
  Register-ScheduledTask -TaskName "SherlockdogsCodexRunner" -Action $RunnerAction -Trigger $RunnerTrigger -Settings $TaskSettings -Description "Sherlockdogs Codex runner" -Force | Out-Null
  Start-ScheduledTask -TaskName "SherlockdogsCodexRunner" -ErrorAction SilentlyContinue

  if ($WindowsWeChatDir -and (Test-Path $WindowsWeChatDir)) {
    $WeChatAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$TaskRunner`" -Kind windows-wechat"
    $WeChatTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds 20) -RepetitionDuration (New-TimeSpan -Days 3650)
    Register-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -Action $WeChatAction -Trigger $WeChatTrigger -Settings $TaskSettings -Description "Sherlockdogs Windows WeChat self-chat DB watcher" -Force | Out-Null
    Start-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -ErrorAction SilentlyContinue
  }
}

Write-Host "Sherlockdogs Windows alpha installed."
Write-Host "Inbox: $InboxDir"
Write-Host "Clipping: $ClippingDir"
Write-Host "Python: $PythonBin"
Write-Host "Config: $ConfigFile"
if ($env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR) { Write-Host "Windows WeChat DB: $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR" }
if ($NoTasks) { Write-Host "Scheduled Tasks generated: skipped (--NoTasks)." }
if ($SkipDeps) { Write-Host "Dependency install skipped (--SkipDeps)." }
