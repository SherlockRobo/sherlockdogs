$ErrorActionPreference = "Continue"

$ConfigDir = Join-Path $env:USERPROFILE ".sherlockdogs"
$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$Fails = 0
$Warnings = 0

function Pass($Message) { Write-Host "PASS $Message" }
function Warn($Message) { $script:Warnings += 1; Write-Host "WARN $Message" }
function Fail($Message) { $script:Fails += 1; Write-Host "FAIL $Message" }

Write-Host "Sherlockdogs preflight"

$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
if ($Python -and (Test-Path $Python)) {
  Pass "python=$Python"
} else {
  Fail "Python not found. Install Python 3, then run Sherlockdogs Start again."
}

try {
  New-Item -ItemType Directory -Force -Path $ConfigDir, $InboxDir | Out-Null
  $ConfigTest = Join-Path $ConfigDir ".write-test"
  $InboxTest = Join-Path $InboxDir ".write-test"
  "ok" | Set-Content -Encoding UTF8 $ConfigTest
  "ok" | Set-Content -Encoding UTF8 $InboxTest
  Remove-Item -Force $ConfigTest, $InboxTest
  Pass "writable config/inbox"
} catch {
  Fail "Cannot write to $ConfigDir or $InboxDir."
}

$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
if ($Codex -and (Test-Path $Codex)) {
  Pass "codex=$Codex"
} else {
  Warn "Codex not found. Install/open Codex before expecting AI chatbox tasks."
}

try {
  Invoke-WebRequest -Uri "https://pypi.org/simple/pip/" -Method Head -TimeoutSec 5 -UseBasicParsing | Out-Null
  Pass "network pypi.org reachable"
} catch {
  Warn "pypi.org not reachable. Dependency install may fail on this network."
}

if (Get-Command ffprobe -ErrorAction SilentlyContinue) {
  Pass "ffprobe available"
} else {
  Warn "ffprobe missing. Video duration/metadata may be limited until ffmpeg is installed."
}

Write-Host "summary fails=$Fails warnings=$Warnings"
if ($Fails -gt 0) { exit 1 }
exit 0
