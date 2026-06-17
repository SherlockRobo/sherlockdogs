param([switch]$Report)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }

$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$VaultDir = if ($env:SHERLOCKDOGS_VAULT_DIR) { $env:SHERLOCKDOGS_VAULT_DIR } else { Join-Path $env:USERPROFILE "ObsidianVault_LOCAL" }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $VaultDir "clipping" }
$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $env:USERPROFILE ".sherlockdogs\venv" }
$Manifest = Join-Path $ProjectDir "packaging\windows-beta\manifest.json"
$WindowsWeChatDir = if ($env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR) { $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR } else { "" }

function Status-Path($p) { if ($p -and (Test-Path $p)) { "ok" } else { "missing" } }
function Status-Module($m) { if (-not $Python) { "missing-python" } else { try { & $Python -c "import $m" *> $null; "ok" } catch { "missing" } } }
function Count-Json($p) { if (Test-Path $p) { @(Get-ChildItem -Path $p -Filter *.json -File -ErrorAction SilentlyContinue).Count } else { 0 } }
function Task-State($name) { $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; if ($t) { $t.State } else { "not registered" } }
function Bin-Status($name) { if (Get-Command $name -ErrorAction SilentlyContinue) { "ok" } elseif (Test-Path (Join-Path $VenvDir "Scripts\$name.exe")) { "ok-venv" } else { "missing" } }

$manifestObj = if (Test-Path $Manifest) { Get-Content $Manifest -Raw | ConvertFrom-Json } else { $null }
$PythonStatus = Status-Path $Python
$CodexStatus = Status-Path $Codex
$RequestsStatus = Status-Module requests
$Bs4Status = Status-Module bs4
$MarkdownifyStatus = Status-Module markdownify
$PilStatus = Status-Module PIL
$YtdlpStatus = Bin-Status yt-dlp
$FfprobeStatus = Bin-Status ffprobe
$LocalTaskState = Task-State SherlockdogsLocalInbox
$RunnerTaskState = Task-State SherlockdogsCodexRunner
$WeChatTaskState = Task-State SherlockdogsWindowsWeChatInbox
$FailedCount = Count-Json (Join-Path $ProjectDir 'jobs\failed')
$WeChatDbCount = if ($WindowsWeChatDir -and (Test-Path $WindowsWeChatDir)) { @(Get-ChildItem -Path $WindowsWeChatDir -Recurse -File -Include "message_*.db","MSG*.db","Msg*.db" -ErrorAction SilentlyContinue).Count } else { 0 }

$lines = @(
  "Sherlockdogs doctor",
  "version=$($manifestObj.version)",
  "channel=$($manifestObj.channel)",
  "project=$ProjectDir status=$(Status-Path $ProjectDir)",
  "manifest=$Manifest status=$(Status-Path $Manifest)",
  "config=$ConfigFile status=$(Status-Path $ConfigFile)",
  "inbox=$InboxDir status=$(Status-Path $InboxDir)",
  "vault=$VaultDir status=$(Status-Path $VaultDir)",
  "clipping=$ClippingDir status=$(Status-Path $ClippingDir)",
  "python=$Python status=$PythonStatus",
  "venv=$VenvDir status=$(Status-Path $VenvDir)",
  "codex=$Codex status=$CodexStatus",
  "module.requests=$RequestsStatus",
  "module.bs4=$Bs4Status",
  "module.markdownify=$MarkdownifyStatus",
  "module.PIL=$PilStatus",
  "binary.yt-dlp=$YtdlpStatus",
  "binary.ffprobe=$FfprobeStatus",
  "task.local-inbox=$LocalTaskState",
  "task.codex-runner=$RunnerTaskState",
  "task.windows-wechat=$WeChatTaskState",
  "windows_wechat_decrypted_dir=$WindowsWeChatDir status=$(Status-Path $WindowsWeChatDir)",
  "windows_wechat_message_dbs=$WeChatDbCount",
  "pending=$(Count-Json (Join-Path $ProjectDir 'jobs\pending'))",
  "running=$(Count-Json (Join-Path $ProjectDir 'jobs\running'))",
  "done=$(Count-Json (Join-Path $ProjectDir 'jobs\done'))",
  "failed=$FailedCount"
)
$Advice = @()
if ($PythonStatus -ne "ok") { $Advice += "- Install Python 3, then run Install Sherlockdogs.cmd again." }
if ($CodexStatus -ne "ok") { $Advice += "- Install/open Codex, or set CODEX_BIN in $ConfigFile." }
if (($RequestsStatus -ne "ok") -or ($Bs4Status -ne "ok") -or ($MarkdownifyStatus -ne "ok") -or ($PilStatus -ne "ok")) {
  $Advice += "- Run Install Sherlockdogs.cmd again to rebuild Python dependencies."
}
if ($FfprobeStatus -eq "missing") { $Advice += "- Video metadata may be limited until ffprobe/ffmpeg is installed." }
if (($LocalTaskState -eq "not registered") -or ($RunnerTaskState -eq "not registered")) {
  $Advice += "- Background tasks are not registered; run Install Sherlockdogs.cmd again."
}
if (-not $WindowsWeChatDir) {
  $Advice += "- Windows WeChat self-chat is not connected; run Sherlockdogs Connect WeChat.cmd after preparing decrypted local WeChat DBs."
} elseif ($WeChatDbCount -eq 0) {
  $Advice += "- Windows WeChat directory has no decrypted message DBs; check the selected directory."
} elseif ($WeChatTaskState -eq "not registered") {
  $Advice += "- Windows WeChat DB directory is configured but watcher task is missing; run Sherlockdogs Connect WeChat.cmd again."
}
if ($FailedCount -ne 0) { $Advice += "- Failed jobs exist; open Diagnostics and send the latest doctor report." }
$lines += "next_steps:"
if ($Advice.Count -eq 0) {
  $lines += "- OK: drop files or links into $InboxDir."
  $lines += "- Results will appear under $ClippingDir."
} else {
  $lines += $Advice
}
$lines | ForEach-Object { Write-Host $_ }
if ($Report) {
  $ReportDir = Join-Path $env:USERPROFILE ".sherlockdogs\diagnostics"
  New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
  $ReportPath = Join-Path $ReportDir ("doctor-{0}.txt" -f (Get-Date -Format yyyyMMdd-HHmmss))
  $lines | Set-Content -Encoding UTF8 $ReportPath
  Write-Host "diagnostic_report=$ReportPath"
}
