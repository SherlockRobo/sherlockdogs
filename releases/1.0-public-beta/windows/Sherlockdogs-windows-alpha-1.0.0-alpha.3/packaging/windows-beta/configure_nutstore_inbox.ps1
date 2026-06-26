param(
  [string]$Path = "",
  [switch]$NoTasks
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigDir = Join-Path $env:USERPROFILE ".sherlockdogs"
$ConfigFile = Join-Path $ConfigDir "config.ps1"

function Find-NutstoreRoot {
  $candidates = @(
    (Join-Path $env:USERPROFILE "Nutstore Files"),
    (Join-Path $env:USERPROFILE "坚果云"),
    (Join-Path $env:USERPROFILE "Nutstore"),
    (Join-Path $env:USERPROFILE "Documents\Nutstore Files"),
    (Join-Path $env:USERPROFILE "Documents\坚果云")
  )
  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
  }
  $found = Get-ChildItem -Path $env:USERPROFILE -Directory -Recurse -Depth 3 -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @("Nutstore Files", "坚果云", "Nutstore") } |
    Select-Object -First 1
  if ($found) { return $found.FullName }
  return ""
}

$NutstoreRoot = if ($Path) { $Path } elseif ($env:SHERLOCKDOGS_NUTSTORE_DIR) { $env:SHERLOCKDOGS_NUTSTORE_DIR } else { Find-NutstoreRoot }
if (-not $NutstoreRoot -or -not (Test-Path $NutstoreRoot)) {
  throw "Nutstore sync folder was not found. Install and sign in to Nutstore first, or rerun with -Path C:\path\to\Nutstore."
}

$NutstoreRoot = (Resolve-Path $NutstoreRoot).Path
$InboxDir = Join-Path $NutstoreRoot "Sherlockdogs\Inbox"
$OutboxDir = Join-Path $NutstoreRoot "Sherlockdogs\Outbox"
New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir, $OutboxDir | Out-Null

if (Test-Path $ConfigFile) { . $ConfigFile }
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

$ConfigLines = @(
  "`$env:SHERLOCKDOGS_PROJECT_DIR = $(Quote-PsString $ProjectDir)",
  "`$env:SHERLOCKDOGS_INBOX_DIR = $(Quote-PsString $InboxDir)",
  "`$env:SHERLOCKDOGS_NUTSTORE_DIR = $(Quote-PsString $NutstoreRoot)",
  "`$env:SHERLOCKDOGS_VAULT_DIR = $(Quote-PsString $VaultDir)",
  "`$env:SHERLOCKDOGS_CLIPPING_DIR = $(Quote-PsString $ClippingDir)",
  "`$env:SHERLOCKDOGS_VENV_DIR = $(Quote-PsString $VenvDir)",
  "`$env:PYTHON_BIN = $(Quote-PsString $Python)",
  "`$env:CODEX_BIN = $(Quote-PsString $Codex)",
  "`$env:PYTHONDONTWRITEBYTECODE = '1'",
  "`$env:PATH = (Join-Path $(Quote-PsString $VenvDir) 'Scripts') + ';' + `$env:PATH"
)
if ($WindowsWeChatDir) { $ConfigLines += "`$env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR = $(Quote-PsString $WindowsWeChatDir)" }
$ConfigLines | Set-Content -Encoding UTF8 $ConfigFile

$install = Join-Path $ProjectDir "packaging\windows-beta\install.ps1"
if (Test-Path $install) {
  $env:SHERLOCKDOGS_INBOX_DIR = $InboxDir
  if ($NoTasks) {
    & $install -SkipDeps -NoTasks *> (Join-Path $env:TEMP "sdogs-nutstore-install.log")
  } else {
    & $install -SkipDeps *> (Join-Path $env:TEMP "sdogs-nutstore-install.log")
  }
}

Start-Process explorer.exe $InboxDir
Write-Host "Sherlockdogs Nutstore Inbox configured."
Write-Host "Nutstore: $NutstoreRoot"
Write-Host "Inbox: $InboxDir"
Write-Host "Config: $ConfigFile"
Write-Host ""
Write-Host "Phone shortcut target folder: /Sherlockdogs/Inbox"
Write-Host "Nutstore WebDAV base: https://dav.jianguoyun.com/dav/"
