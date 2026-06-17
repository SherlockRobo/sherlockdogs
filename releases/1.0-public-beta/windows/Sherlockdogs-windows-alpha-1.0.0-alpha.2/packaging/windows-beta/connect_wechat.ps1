param(
  [string]$DecryptedDbDir = "",
  [string]$Receivers = "filehelper",
  [switch]$NoTask
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigDir = Join-Path $env:USERPROFILE ".sherlockdogs"
$ConfigFile = Join-Path $ConfigDir "config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$VaultDir = if ($env:SHERLOCKDOGS_VAULT_DIR) { $env:SHERLOCKDOGS_VAULT_DIR } elseif (Test-Path (Join-Path $env:USERPROFILE "ObsidianVault_LOCAL")) { Join-Path $env:USERPROFILE "ObsidianVault_LOCAL" } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault" }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $VaultDir "clipping" }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $ConfigDir "venv" }

if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first, or install Python 3." }
if (-not (Test-Path $Python)) { throw "Configured Python does not exist: $Python" }

if (-not $DecryptedDbDir) {
  $DefaultDir = Join-Path $ConfigDir "windows-wechat-decrypted"
  Write-Host "Choose the decrypted Windows WeChat DB directory containing message\message_*.db."
  Write-Host "Default: $DefaultDir"
  $InputDir = Read-Host "Decrypted WeChat DB directory"
  if ($InputDir) { $DecryptedDbDir = $InputDir } else { $DecryptedDbDir = $DefaultDir }
}

$ResolvedDbDir = Resolve-Path $DecryptedDbDir -ErrorAction SilentlyContinue
if (-not $ResolvedDbDir) { throw "Decrypted WeChat DB directory not found: $DecryptedDbDir" }
$DecryptedDbDir = $ResolvedDbDir.Path

$MessageDbs = @(Get-ChildItem -Path $DecryptedDbDir -Recurse -File -Include "message_*.db","MSG*.db","Msg*.db" -ErrorAction SilentlyContinue)
if ($MessageDbs.Count -eq 0) { throw "No decrypted WeChat message DB found under: $DecryptedDbDir" }

New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir, $ClippingDir, (Join-Path $ProjectDir "jobs\pending"), (Join-Path $ProjectDir "jobs\running"), (Join-Path $ProjectDir "jobs\done"), (Join-Path $ProjectDir "jobs\failed"), (Join-Path $ProjectDir "runs") | Out-Null

$ReceiverFile = Join-Path $ProjectDir "jobs\windows_receiver_chats.txt"
$ReceiverLines = $Receivers.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($ReceiverLines.Count -eq 0) { $ReceiverLines = @("filehelper") }
$ReceiverLines | Set-Content -Encoding UTF8 $ReceiverFile

@"
`$env:SHERLOCKDOGS_PROJECT_DIR = '$ProjectDir'
`$env:SHERLOCKDOGS_INBOX_DIR = '$InboxDir'
`$env:SHERLOCKDOGS_VAULT_DIR = '$VaultDir'
`$env:SHERLOCKDOGS_CLIPPING_DIR = '$ClippingDir'
`$env:SHERLOCKDOGS_VENV_DIR = '$VenvDir'
`$env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR = '$DecryptedDbDir'
`$env:PYTHON_BIN = '$Python'
`$env:CODEX_BIN = '$Codex'
`$env:PYTHONDONTWRITEBYTECODE = '1'
`$env:PATH = (Join-Path '$VenvDir' 'Scripts') + ';' + `$env:PATH
"@ | Set-Content -Encoding UTF8 $ConfigFile

& $Python (Join-Path $ProjectDir "scripts\windows_wechat_inbox.py") --once --dry-run --settle-seconds 0 --db-root $DecryptedDbDir
if ($LASTEXITCODE -ne 0) { throw "Windows WeChat adapter dry-run failed." }

if (-not $NoTask) {
  $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command `. '$ConfigFile'; `$env:PYTHONDONTWRITEBYTECODE='1'; & '$Python' '$ProjectDir\scripts\windows_wechat_inbox.py' --db-root '$DecryptedDbDir'"
  $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds 20) -RepetitionDuration (New-TimeSpan -Days 3650)
  Register-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -Action $Action -Trigger $Trigger -Description "Sherlockdogs Windows WeChat self-chat DB watcher" -Force | Out-Null
}

Write-Host "Sherlockdogs Windows WeChat adapter connected."
Write-Host "Decrypted WeChat DB: $DecryptedDbDir"
Write-Host "Receivers: $($ReceiverLines -join ', ')"
Write-Host "Task: $(if ($NoTask) { 'skipped' } else { 'SherlockdogsWindowsWeChatInbox' })"
