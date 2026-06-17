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
$NutstoreDir = if ($env:SHERLOCKDOGS_NUTSTORE_DIR) { $env:SHERLOCKDOGS_NUTSTORE_DIR } else { "" }
$VaultDir = if ($env:SHERLOCKDOGS_VAULT_DIR) { $env:SHERLOCKDOGS_VAULT_DIR } elseif (Test-Path (Join-Path $env:USERPROFILE "ObsidianVault_LOCAL")) { Join-Path $env:USERPROFILE "ObsidianVault_LOCAL" } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault" }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $VaultDir "clipping" }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $ConfigDir "venv" }
$ToolRoot = Join-Path $ConfigDir "tools"
$WeChatDecryptDir = Join-Path $ToolRoot "wechat-decrypt"
$DiagnosticsDir = Join-Path $ConfigDir "diagnostics"
New-Item -ItemType Directory -Force -Path $DiagnosticsDir | Out-Null
$ConnectReport = Join-Path $DiagnosticsDir ("windows-wechat-connect-{0}.txt" -f (Get-Date -Format yyyyMMdd-HHmmss))
@(
  "Sherlockdogs Windows WeChat connect",
  "started_at=$(Get-Date -Format o)",
  "project=$ProjectDir",
  "config=$ConfigFile",
  "receivers=$Receivers",
  "no_task=$NoTask",
  "no_decrypt_bootstrap=$NoDecryptBootstrap"
) | Set-Content -Encoding UTF8 $ConnectReport

function Add-ConnectReport([string]$Line) {
  Add-Content -Encoding UTF8 -Path $ConnectReport -Value $Line
}

if (-not $Python) {
  Add-ConnectReport "status=failed"
  Add-ConnectReport "error=python_not_found"
  throw "Python not found. Run Sherlockdogs Start.cmd first, or install Python 3."
}
if (-not (Test-Path $Python)) {
  Add-ConnectReport "status=failed"
  Add-ConnectReport "error=configured_python_missing"
  Add-ConnectReport "python=$Python"
  throw "Configured Python does not exist: $Python"
}
Add-ConnectReport "python=$Python"

function Quote-PsString([string]$Value) {
  return "'" + (($Value -as [string]) -replace "'", "''") + "'"
}

function Test-Admin {
  try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  } catch {
    return $false
  }
}

function Get-MessageDbs([string]$Root) {
  if (-not $Root -or -not (Test-Path $Root)) { return @() }
  return @(Get-ChildItem -Path $Root -Recurse -File -Include "message.db","message*.db","Message*.db","MSG*.db","Msg*.db" -ErrorAction SilentlyContinue)
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
  $MainPy = Join-Path $WeChatDecryptDir "main.py"
  if ((Test-Path $WeChatDecryptDir) -and -not (Test-Path $MainPy)) {
    $BrokenDir = "$WeChatDecryptDir.broken-$(Get-Date -Format yyyyMMdd-HHmmss)"
    Write-DecryptLog $DecryptLog "Existing helper is incomplete; moving it to $BrokenDir"
    Move-Item -Path $WeChatDecryptDir -Destination $BrokenDir -Force
  }
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
  $GitForVersion = Get-Command git -ErrorAction SilentlyContinue
  if ($GitForVersion -and (Test-Path (Join-Path $WeChatDecryptDir ".git"))) {
    try {
      $HelperCommit = (& $GitForVersion.Source -C $WeChatDecryptDir rev-parse --short HEAD 2>$null | Select-Object -First 1)
      if ($HelperCommit) { Write-DecryptLog $DecryptLog "helper_commit=$HelperCommit" }
    } catch {
      Write-DecryptLog $DecryptLog "helper_commit=unknown"
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

  Write-DecryptLog $DecryptLog "Checking wechat-decrypt status before decrypt..."
  try {
    & $Python $MainPy status 2>&1 | Tee-Object -FilePath $DecryptLog -Append
    Add-Content -Encoding UTF8 -Path $DecryptLog -Value "status_exit=$LASTEXITCODE"
  } catch {
    Add-Content -Encoding UTF8 -Path $DecryptLog -Value "status_failed=$($_.Exception.Message)"
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
    Add-ConnectReport "db_source=existing"
    Add-ConnectReport "existing_db_root=$Existing"
  } elseif (-not $NoDecryptBootstrap) {
    if (-not (Test-Admin)) {
      Add-ConnectReport "status=failed"
      Add-ConnectReport "error=admin_required_for_decrypt_bootstrap"
      throw "Windows WeChat decrypt bootstrap needs Administrator PowerShell to read the WeChat process key. Right-click Sherlockdogs Connect WeChat.cmd and choose Run as administrator, or pass -DecryptedDbDir to an existing decrypted DB folder."
    }
    Add-ConnectReport "db_source=decrypt_bootstrap"
    $DecryptedDbDir = Invoke-WeChatDecryptBootstrap
  } else {
    Write-Host "Choose the decrypted Windows WeChat DB directory containing message\message_*.db."
    Write-Host "Default: $DefaultDir"
    $InputDir = Read-Host "Decrypted WeChat DB directory"
    if ($InputDir) { $DecryptedDbDir = $InputDir } else { $DecryptedDbDir = $DefaultDir }
  }
}

$ResolvedDbDir = Resolve-Path $DecryptedDbDir -ErrorAction SilentlyContinue
if (-not $ResolvedDbDir) {
  Add-ConnectReport "status=failed"
  Add-ConnectReport "error=db_root_missing"
  Add-ConnectReport "decrypted_db_dir=$DecryptedDbDir"
  throw "Decrypted WeChat DB directory not found: $DecryptedDbDir"
}
$DecryptedDbDir = $ResolvedDbDir.Path
Add-ConnectReport "decrypted_db_dir=$DecryptedDbDir"

$MessageDbs = Get-MessageDbs $DecryptedDbDir
Add-ConnectReport "message_db_count=$($MessageDbs.Count)"
foreach ($Db in ($MessageDbs | Select-Object -First 10)) {
  Add-ConnectReport "message_db=$($Db.FullName)"
}
if ($MessageDbs.Count -eq 0) {
  Add-ConnectReport "status=failed"
  Add-ConnectReport "error=no_message_db"
  throw "No decrypted WeChat message DB found under: $DecryptedDbDir"
}

New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir, $ClippingDir, (Join-Path $ProjectDir "jobs\pending"), (Join-Path $ProjectDir "jobs\running"), (Join-Path $ProjectDir "jobs\done"), (Join-Path $ProjectDir "jobs\failed"), (Join-Path $ProjectDir "runs") | Out-Null

$ReceiverFile = Join-Path $ProjectDir "jobs\windows_receiver_chats.txt"
$ReceiverLines = $Receivers.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($ReceiverLines.Count -eq 0) { $ReceiverLines = @("filehelper") }
$ReceiverLines | Set-Content -Encoding UTF8 $ReceiverFile
Add-ConnectReport "receiver_file=$ReceiverFile"
Add-ConnectReport "receiver_lines=$($ReceiverLines -join ',')"

$ConfigLines = @(
  "`$env:SHERLOCKDOGS_PROJECT_DIR = $(Quote-PsString $ProjectDir)",
  "`$env:SHERLOCKDOGS_INBOX_DIR = $(Quote-PsString $InboxDir)",
  "`$env:SHERLOCKDOGS_VAULT_DIR = $(Quote-PsString $VaultDir)",
  "`$env:SHERLOCKDOGS_CLIPPING_DIR = $(Quote-PsString $ClippingDir)",
  "`$env:SHERLOCKDOGS_VENV_DIR = $(Quote-PsString $VenvDir)",
  "`$env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR = $(Quote-PsString $DecryptedDbDir)",
  "`$env:PYTHON_BIN = $(Quote-PsString $Python)",
  "`$env:CODEX_BIN = $(Quote-PsString $Codex)",
  "`$env:PYTHONDONTWRITEBYTECODE = '1'",
  "`$env:PATH = (Join-Path $(Quote-PsString $VenvDir) 'Scripts') + ';' + `$env:PATH"
)
if ($NutstoreDir) { $ConfigLines += "`$env:SHERLOCKDOGS_NUTSTORE_DIR = $(Quote-PsString $NutstoreDir)" }
$ConfigLines | Set-Content -Encoding UTF8 $ConfigFile

$DryRunOutput = & $Python (Join-Path $ProjectDir "scripts\windows_wechat_inbox.py") --once --dry-run --settle-seconds 0 --db-root $DecryptedDbDir 2>&1
$DryRunExit = $LASTEXITCODE
Add-ConnectReport "adapter_dry_run_exit=$DryRunExit"
Add-ConnectReport "adapter_dry_run_output_begin"
$DryRunOutput | ForEach-Object { Add-ConnectReport $_ }
Add-ConnectReport "adapter_dry_run_output_end"
Write-Host ($DryRunOutput | Out-String)
if ($DryRunExit -ne 0) {
  Add-ConnectReport "status=failed"
  Add-ConnectReport "error=adapter_dry_run_failed"
  throw "Windows WeChat adapter dry-run failed."
}

if (-not $NoTask) {
  $TaskRunner = Join-Path $ProjectDir "packaging\windows-beta\task_runner.ps1"
  $WatcherTaskSettings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
  $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$TaskRunner`" -Kind windows-wechat"
  $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Seconds 20) -RepetitionDuration (New-TimeSpan -Days 3650)
  Register-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -Action $Action -Trigger $Trigger -Settings $WatcherTaskSettings -Description "Sherlockdogs Windows WeChat self-chat DB watcher" -Force | Out-Null
  Start-ScheduledTask -TaskName "SherlockdogsWindowsWeChatInbox" -ErrorAction SilentlyContinue
  Add-ConnectReport "task=SherlockdogsWindowsWeChatInbox"
  Add-ConnectReport "task_registered=ok"
} else {
  Add-ConnectReport "task=skipped"
}

Add-ConnectReport "status=ok"
Add-ConnectReport "finished_at=$(Get-Date -Format o)"
Write-Host "Sherlockdogs Windows WeChat adapter connected."
Write-Host "Decrypted WeChat DB: $DecryptedDbDir"
Write-Host "Receivers: $($ReceiverLines -join ', ')"
Write-Host "Task: $(if ($NoTask) { 'skipped' } else { 'SherlockdogsWindowsWeChatInbox' })"
Write-Host "Connect report: $ConnectReport"
