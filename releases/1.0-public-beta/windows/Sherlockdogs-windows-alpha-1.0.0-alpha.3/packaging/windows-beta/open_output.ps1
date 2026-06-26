$ErrorActionPreference = "Stop"
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }
$OutputDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) {
  $env:SHERLOCKDOGS_CLIPPING_DIR
} else {
  $DefaultVault = Join-Path $env:USERPROFILE "ObsidianVault_LOCAL"
  if (Test-Path $DefaultVault) {
    Join-Path $DefaultVault "clipping"
  } else {
    Join-Path $env:USERPROFILE "Sherlockdogs\Vault\clipping"
  }
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
Start-Process explorer.exe $OutputDir
Write-Host "Opened Output: $OutputDir"
