param(
  [string]$DecryptedDbDir = "",
  [string]$Receivers = "*",
  [switch]$NoTask,
  [switch]$NoDecryptBootstrap,
  [string]$WeChatDecryptRepo = "https://github.com/ylytdeng/wechat-decrypt.git",
  [string]$WeChatDecryptZipUrl = "https://github.com/ylytdeng/wechat-decrypt/archive/refs/heads/main.zip"
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
$ToolRoot = Join-Path $ConfigDir "tools"
$WeChatDecryptDir = Join-Path $ToolRoot "wechat-decrypt"
$DiagnosticsDir = Join-Path $ConfigDir "diagnostics"

if (-not $Python) { throw "Python not found. Run Sherlockdogs Start.cmd first, or install Python 3." }
if (-not (Test-Path $Python)) { throw "Configured Python does not exist: $Python" }

function Get-MessageDbs([string]$Root) {
  if (-not $Root -or -not (Test-Path $Root)) { return @() }
  return @(Get-ChildItem -Path $Root -Recurse -File -Include "message_*.db","MSG*.db","Msg*.db" -ErrorAction SilentlyContinue)
}

function Resolve-MessageDbRoot($FileInfo) {
  $dir = $FileInfo.Directory
  if ($dir -and ($dir.Name -ieq "message") -and $dir.Parent) {
    return $dir.Parent.FullName
  }
  return $dir.FullName
}

function Find-DecryptedDbRoot([string[]]$Roots) {
  foreach ($Root in $Roots) {
    $dbs = Get-MessageDbs $Root
    if ($dbs.Count -gt 0) {
      return Resolve-MessageDbRoot $dbs[0]
    }
  }
  return ""
}

function New-DecryptLog {
  New-Item -ItemType Directory -Force -Path $DiagnosticsDir | Out-Null
  $path = Join-Path $DiagnosticsDir ("wechat-decrypt-{0}.log" -f (Get-Date -Format yyyyMMdd-HHmmss))
  @(
    "Sherlockdogs Windows WeChat decrypt bootstrap",
    "started_at=$(Get-Date -Format o)",
    "project=$ProjectDir",
    "helper=$WeChatDecryptDir",
    "python=$Python"
  ) | Set-Content -Encoding UTF8 $path
  return $path
}

function Write-DecryptLog([string]$LogPath, [string]$Message) {
  $line = "{0} {1}" -f (Get-Date -Format o), $Message
  Add-Content -Encoding UTF8 -Path $LogPath -Value $line
  Write-Host $Message
}

function Invoke-WeChatDecryptBootstrap {
  New-Item -ItemType Directory -Force -Path $ToolRoot | Out-Null
  $DecryptLog = New-DecryptLog
  Write-DecryptLog $DecryptLog "decrypt_log=$DecryptLog"
  if (-not (Test-Path $WeChatDecryptDir)) {
    $Git = Get-Command git -ErrorAction SilentlyContinue
    if ($Git) {
      Write-DecryptLog $DecryptLog "Installing local helper: wechat-decrypt"
      & $Git.Source clone --depth 1 $WeChatDecryptRepo $WeChatDecryptDir 2>&1 | Tee-Object -FilePath $DecryptLog -Append
      $CloneExit = $LASTEXITCODE
      Add-Content -Encoding UTF8 -Path $DecryptLog -Value "git_clone_exit=$CloneExit"
      if ($CloneExit -ne 0) { throw "Failed to clone wechat-decrypt helper. Log: $DecryptLog" }
    } else {
      $ZipPath = Join-Path $ToolRoot "wechat-decrypt-main.zip"
      $ExtractDir = Join-Path $ToolRoot "wechat-decrypt-main"
      Write-DecryptLog $DecryptLog "Git is not available. Downloading local helper archive: $WeChatDecryptZipUrl"
      Invoke-WebRequest -Uri $WeChatDecryptZipUrl -OutFile $ZipPath
      Add-Content -Encoding UTF8 -Path $DecryptLog -Value "downloaded_zip=$ZipPath"
      if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
      Expand-Archive -Path $ZipPath -DestinationPath $ToolRoot -Force
      Add-Content -Encoding UTF8 -Path $DecryptLog -Value "expanded_zip=$ZipPath"
      if (-not (Test-Path $ExtractDir)) {
        $ExtractDir = Get-ChildItem -Path $ToolRoot -Directory -Filter "wechat-decrypt-*" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
      }
      if (-not $ExtractDir -or -not (Test-Path $ExtractDir)) {
        throw "No decrypted DB found, and the helper archive could not be expanded. Install Git, or manually place decrypted DBs under $ConfigDir\windows-wechat-decrypted. Log: $DecryptLog"
      }
      Move-Item -Path $ExtractDir -Destination $WeChatDecryptDir -Force
      Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue
      Add-Content -Encoding UTF8 -Path $DecryptLog -Value "helper_dir=$WeChatDecryptDir"
    }
  }

  $Requirements = Join-Path $WeChatDecryptDir "requirements.txt"
  if (Test-Path $Requirements) {
    Write-DecryptLog $DecryptLog "Installing wechat-decrypt Python dependencies..."
    & $Python -m pip install -r $Requirements 2>&1 | Tee-Object -FilePath $DecryptLog -Append
    $PipExit = $LASTEXITCODE
    Add-Content -Encoding UTF8 -Path $DecryptLog -Value "pip_install_exit=$PipExit"
    if ($PipExit -ne 0) { throw "Failed to install wechat-decrypt dependencies. Log: $DecryptLog" }
  }

  $MainPy = Join-Path $WeChatDecryptDir "main.py"
  if (-not (Test-Path $MainPy)) {
    throw "wechat-decrypt helper is missing main.py: $WeChatDecryptDir. Log: $DecryptLog"
  }

  Write-DecryptLog $DecryptLog "Running local WeChat decrypt helper. Keep Windows WeChat logged in. Administrator PowerShell may be required for key extraction."
  Push-Location $WeChatDecryptDir
  try {
    & $Python $MainPy decrypt 2>&1 | Tee-Object -FilePath $DecryptLog -Append
    $DecryptExit = $LASTEXITCODE
    Add-Content -Encoding UTF8 -Path $DecryptLog -Value "decrypt_exit=$DecryptExit"
    if ($DecryptExit -ne 0) { throw "wechat-decrypt returned exit code $DecryptExit. Log: $DecryptLog" }
  } finally {
    Pop-Location
  }

  $Found = Find-DecryptedDbRoot @($WeChatDecryptDir, (Join-Path $ConfigDir "windows-wechat-decrypted"), $ConfigDir)
  if (-not $Found) {
    throw "Decrypt helper finished, but no message_*.db / MSG*.db was found. Run Doctor Sherlockdogs.cmd and check the helper output under $WeChatDecryptDir. Log: $DecryptLog"
  }
  Add-Content -Encoding UTF8 -Path $DecryptLog -Value "found_db_root=$Found"
  return $Found
}

if (-not $DecryptedDbDir) {
  $DefaultDir = Join-Path $ConfigDir "windows-wechat-decrypted"
  $Existing = Find-DecryptedDbRoot @($DefaultDir, $WeChatDecryptDir, $ConfigDir)
  if ($Existing) {
    $DecryptedDbDir = $Existing
  } elseif (-not $NoDecryptBootstrap) {
    $DecryptedDbDir = Invoke-WeChatDecryptBootstrap
  } else {
    Write-Host "Choose the decrypted Windows WeChat DB directory containing message\message_*.db."
    Write-Host "Default: $DefaultDir"
    $InputDir = Read-Host "Decrypted WeChat DB directory"
    if ($InputDir) { $DecryptedDbDir = $InputDir } else { $DecryptedDbDir = $DefaultDir }
  }
}

$ResolvedDbDir = Resolve-Path $DecryptedDbDir -ErrorAction SilentlyContinue
if (-not $ResolvedDbDir) { throw "Decrypted WeChat DB directory not found: $DecryptedDbDir" }
$DecryptedDbDir = $ResolvedDbDir.Path

$MessageDbs = Get-MessageDbs $DecryptedDbDir
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
  Start-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -ErrorAction SilentlyContinue
}

Write-Host "Sherlockdogs Windows WeChat adapter connected."
Write-Host "Decrypted WeChat DB: $DecryptedDbDir"
Write-Host "Receivers: $($ReceiverLines -join ', ')"
Write-Host "Task: $(if ($NoTask) { 'skipped' } else { 'SherlockdogsWindowsWeChatInbox' })"
