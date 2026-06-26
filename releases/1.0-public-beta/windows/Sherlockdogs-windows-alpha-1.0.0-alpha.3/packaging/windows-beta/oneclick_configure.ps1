param([switch]$SkipWeChat)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigDir = Join-Path $env:USERPROFILE ".sherlockdogs"
$ConfigFile = Join-Path $ConfigDir "config.ps1"
$InstallScript = Join-Path $PSScriptRoot "install.ps1"
$ConnectScript = Join-Path $PSScriptRoot "connect_wechat.ps1"
$DoctorScript = Join-Path $PSScriptRoot "doctor.ps1"

function Quote-PsString([string]$Value) {
  return "'" + (($Value -as [string]) -replace "'", "''") + "'"
}

function Write-Utf8NoBomLines([string]$Path, [string[]]$Lines) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllLines($Path, $Lines, [System.Text.UTF8Encoding]::new($false))
}

function Add-UniquePath([System.Collections.ArrayList]$List, [string]$Path) {
  if (-not $Path) { return }
  $expanded = [Environment]::ExpandEnvironmentVariables($Path).Trim()
  if (-not $expanded) { return }
  foreach ($item in $List) {
    if ($item -ieq $expanded) { return }
  }
  [void]$List.Add($expanded)
}

function Get-ObsidianVaultCandidates {
  $items = [System.Collections.ArrayList]::new()
  $obsidianJson = Join-Path $env:APPDATA "obsidian\obsidian.json"
  if (Test-Path $obsidianJson) {
    try {
      $data = Get-Content -Raw -Encoding UTF8 $obsidianJson | ConvertFrom-Json
      if ($data.vaults) {
        $props = @($data.vaults.PSObject.Properties)
        $openFirst = @($props | Sort-Object @{Expression = { if ($_.Value.open) { 0 } else { 1 } }}, Name)
        foreach ($prop in $openFirst) {
          Add-UniquePath $items ([string]$prop.Value.path)
        }
      }
    } catch {
      Write-Host "Obsidian config read failed: $($_.Exception.Message)"
    }
  }
  return $items
}

function Get-CommonVaultCandidates {
  $items = [System.Collections.ArrayList]::new()
  if ($env:SHERLOCKDOGS_VAULT_DIR) { Add-UniquePath $items $env:SHERLOCKDOGS_VAULT_DIR }
  foreach ($path in Get-ObsidianVaultCandidates) { Add-UniquePath $items $path }

  $documents = [Environment]::GetFolderPath("MyDocuments")
  $vaultRoot = Join-Path $documents "VAULT"
  if (Test-Path $vaultRoot) {
    $children = @(Get-ChildItem -Path $vaultRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name)
    foreach ($child in $children) { Add-UniquePath $items $child.FullName }
    Add-UniquePath $items $vaultRoot
  }
  Add-UniquePath $items (Join-Path $env:USERPROFILE "ObsidianVault_LOCAL")
  Add-UniquePath $items (Join-Path $env:USERPROFILE "Sherlockdogs\Vault")
  return $items
}

function Select-VaultDir {
  $candidates = Get-CommonVaultCandidates
  Write-Host ""
  Write-Host "Choose the Obsidian vault folder."
  Write-Host "This is the folder you open in Obsidian. Sherlockdogs will write to <vault>\clipping."
  for ($i = 0; $i -lt $candidates.Count; $i++) {
    $n = $i + 1
    $exists = if (Test-Path $candidates[$i]) { "ok" } else { "new" }
    Write-Host "[$n] $($candidates[$i]) ($exists)"
  }
  $answer = Read-Host "Vault number or full path. Press Enter for [1]"
  if (-not $answer) {
    if ($candidates.Count -gt 0) { return [string]$candidates[0] }
    return (Join-Path $env:USERPROFILE "Sherlockdogs\Vault")
  }
  $number = 0
  if ([int]::TryParse($answer, [ref]$number) -and $number -ge 1 -and $number -le $candidates.Count) {
    return [string]$candidates[$number - 1]
  }
  return [Environment]::ExpandEnvironmentVariables($answer.Trim())
}

Write-Host "Sherlockdogs OneClick Configure"
Write-Host "project=$ProjectDir"

if (-not (Test-Path $ConfigFile)) {
  if (-not (Test-Path $InstallScript)) { throw "Install script missing: $InstallScript" }
  Write-Host "Config missing. Running install first..."
  & $InstallScript
  if ($LASTEXITCODE -ne 0) { throw "Install failed before configuration." }
}
if (Test-Path $ConfigFile) { . $ConfigFile }

$VaultDir = Select-VaultDir
$ClippingDir = Join-Path $VaultDir "clipping"
$WorkDir = Join-Path $ClippingDir "_sherlockdogs"
$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $ConfigDir "venv" }
$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { Join-Path $VenvDir "Scripts\python.exe" }
if (-not (Test-Path $Python)) {
  $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
  if ($PythonCmd) { $Python = $PythonCmd.Source }
}
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
if (-not $Codex) { $Codex = "codex" }
$WindowsWeChatDir = if ($env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR) { $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR } else { "" }
$NutstoreDir = if ($env:SHERLOCKDOGS_NUTSTORE_DIR) { $env:SHERLOCKDOGS_NUTSTORE_DIR } else { "" }

New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir, $VaultDir, $ClippingDir, $WorkDir, (Join-Path $WorkDir "jobs\pending"), (Join-Path $WorkDir "jobs\running"), (Join-Path $WorkDir "jobs\done"), (Join-Path $WorkDir "jobs\failed"), (Join-Path $WorkDir "runs") | Out-Null

$ConfigLines = @(
  "`$env:SHERLOCKDOGS_PROJECT_DIR = $(Quote-PsString $ProjectDir)",
  "`$env:SHERLOCKDOGS_INBOX_DIR = $(Quote-PsString $InboxDir)",
  "`$env:SHERLOCKDOGS_VAULT_DIR = $(Quote-PsString $VaultDir)",
  "`$env:SHERLOCKDOGS_CLIPPING_DIR = $(Quote-PsString $ClippingDir)",
  "`$env:SHERLOCKDOGS_WORK_DIR = $(Quote-PsString $WorkDir)",
  "`$env:SHERLOCKDOGS_VENV_DIR = $(Quote-PsString $VenvDir)",
  "`$env:PYTHON_BIN = $(Quote-PsString $Python)",
  "`$env:CODEX_BIN = $(Quote-PsString $Codex)",
  "`$env:PYTHONDONTWRITEBYTECODE = '1'",
  "`$env:PATH = (Join-Path $(Quote-PsString $VenvDir) 'Scripts') + ';' + `$env:PATH"
)
if ($NutstoreDir) { $ConfigLines += "`$env:SHERLOCKDOGS_NUTSTORE_DIR = $(Quote-PsString $NutstoreDir)" }
if ($WindowsWeChatDir) { $ConfigLines += "`$env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR = $(Quote-PsString $WindowsWeChatDir)" }
Write-Utf8NoBomLines $ConfigFile $ConfigLines

Write-Host ""
Write-Host "Configured paths:"
Write-Host "Vault: $VaultDir"
Write-Host "Output: $ClippingDir"
Write-Host "Work: $WorkDir"
Write-Host "Inbox: $InboxDir"
Write-Host "Config: $ConfigFile"
Write-Host ""
Write-Host "Obsidian: open this folder as a vault:"
Write-Host $VaultDir

if (-not $SkipWeChat) {
  if (-not (Test-Path $ConnectScript)) { throw "Connect script missing: $ConnectScript" }
  Write-Host ""
  Write-Host "Now connecting Windows WeChat. Keep Windows WeChat logged in."
  & $ConnectScript -Receivers "*"
  if ($LASTEXITCODE -ne 0) { throw "Connect WeChat failed." }
}

if (Test-Path $DoctorScript) {
  & $DoctorScript -Report
}
