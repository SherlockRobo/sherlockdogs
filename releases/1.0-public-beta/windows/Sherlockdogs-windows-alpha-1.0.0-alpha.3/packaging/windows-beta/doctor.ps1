param([switch]$Report)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }

$InboxDir = if ($env:SHERLOCKDOGS_INBOX_DIR) { $env:SHERLOCKDOGS_INBOX_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Inbox" }
$VaultDir = if ($env:SHERLOCKDOGS_VAULT_DIR) { $env:SHERLOCKDOGS_VAULT_DIR } else { Join-Path $env:USERPROFILE "ObsidianVault_LOCAL" }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $VaultDir "clipping" }
$WorkDir = if ($env:SHERLOCKDOGS_WORK_DIR) { $env:SHERLOCKDOGS_WORK_DIR } else { Join-Path $ClippingDir "_sherlockdogs" }
$Python = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { (Get-Command python -ErrorAction SilentlyContinue).Source }
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
$VenvDir = if ($env:SHERLOCKDOGS_VENV_DIR) { $env:SHERLOCKDOGS_VENV_DIR } else { Join-Path $env:USERPROFILE ".sherlockdogs\venv" }
$Manifest = Join-Path $ProjectDir "packaging\windows-beta\manifest.json"
$WindowsWeChatDir = if ($env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR) { $env:SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR } else { "" }
$ReceiverFile = Join-Path $WorkDir "jobs\windows_receiver_chats.txt"
$WindowsInboxEventsDir = Join-Path $WorkDir "jobs\inbox-events"
$WindowsRunEvents = Join-Path $WorkDir "runs\windows-wechat-inbox.events.jsonl"
$WindowsEvidenceDir = Join-Path $ProjectDir "evidence\windows-wechat-db-smoke"
$WeChatDecryptDir = Join-Path $env:USERPROFILE ".sherlockdogs\tools\wechat-decrypt"
$WindowsInboxScript = Join-Path $ProjectDir "scripts\windows_wechat_inbox.py"
$DiagnosticsDir = Join-Path $env:USERPROFILE ".sherlockdogs\diagnostics"

function Status-Path($p) { if ($p -and (Test-Path $p)) { "ok" } else { "missing" } }
function Status-Module($m) { if (-not $Python) { "missing-python" } else { try { & $Python -c "import $m" *> $null; "ok" } catch { "missing" } } }
function Count-Json($p) { if (Test-Path $p) { @(Get-ChildItem -Path $p -Filter *.json -File -ErrorAction SilentlyContinue).Count } else { 0 } }
function Count-Files($p, $filter) { if (Test-Path $p) { @(Get-ChildItem -Path $p -Filter $filter -File -ErrorAction SilentlyContinue).Count } else { 0 } }
function Latest-File($p, $filter) {
  if (-not (Test-Path $p)) { return "missing" }
  $latest = Get-ChildItem -Path $p -Filter $filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($latest) { return $latest.FullName }
  return "missing"
}
function Evidence-Field($path, $field) {
  if (-not $path -or $path -eq "missing" -or -not (Test-Path $path)) { return "missing" }
  $line = Get-Content $path -ErrorAction SilentlyContinue | Where-Object { $_ -like "$field=*" } | Select-Object -First 1
  if ($line) { return ($line -replace "^$field=", "").Trim() }
  return "missing"
}
function Task-State($name) { $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; if ($t) { $t.State } else { "not registered" } }
function Task-LastResult($name) {
  try {
    $info = Get-ScheduledTaskInfo -TaskName $name -ErrorAction Stop
    return $info.LastTaskResult
  } catch {
    return "missing"
  }
}
function Task-LastRun($name) {
  try {
    $info = Get-ScheduledTaskInfo -TaskName $name -ErrorAction Stop
    if ($info.LastRunTime) { return $info.LastRunTime.ToString("o") }
    return "never"
  } catch {
    return "missing"
  }
}
function Bin-Status($name) { if (Get-Command $name -ErrorAction SilentlyContinue) { "ok" } elseif (Test-Path (Join-Path $VenvDir "Scripts\$name.exe")) { "ok-venv" } else { "missing" } }
function Receiver-Chats($path) {
  if (-not (Test-Path $path)) { return "missing" }
  $items = @(Get-Content $path -ErrorAction SilentlyContinue | ForEach-Object { ($_.Replace([char]0xFEFF, "")).Trim() } | Where-Object { $_ } | Select-Object -First 5)
  if ($items.Count -eq 0) { return "empty" }
  return ($items -join ",")
}
function Admin-Status {
  try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { return "yes" }
    return "no"
  } catch {
    return "unknown"
  }
}
function Process-Status($names) {
  foreach ($name in $names) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) { return "ok:$name" }
  }
  return "missing"
}
function Adapter-DryRun {
  if (-not $Python -or -not (Test-Path $Python)) { return "missing-python" }
  if (-not (Test-Path $WindowsInboxScript)) { return "missing-script" }
  if (-not $WindowsWeChatDir -or -not (Test-Path $WindowsWeChatDir)) { return "missing-db-root" }
  try {
    $output = & $Python $WindowsInboxScript --once --dry-run --db-root $WindowsWeChatDir --receivers "*" --settle-seconds 0 --limit 20 2>&1
    if ($LASTEXITCODE -eq 0) {
      try {
        $json = ($output | Select-Object -Last 1) | ConvertFrom-Json
        $dbErrors = @($json.db_errors)
        if ($dbErrors.Count -gt 0) { return "warn:$($dbErrors[0])" }
      } catch {
      }
      return "ok"
    }
    return "failed:$($output | Select-Object -First 1)"
  } catch {
    return "failed:$($_.Exception.Message)"
  }
}

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
$FailedCount = Count-Json (Join-Path $WorkDir 'jobs\failed')
$WeChatDbCount = if ($WindowsWeChatDir -and (Test-Path $WindowsWeChatDir)) { @(Get-ChildItem -Path $WindowsWeChatDir -Recurse -File -Include "message.db","message*.db","Message*.db","MSG*.db","Msg*.db" -ErrorAction SilentlyContinue).Count } else { 0 }
$ReceiverChats = Receiver-Chats $ReceiverFile
$WindowsInboxEventCount = Count-Json $WindowsInboxEventsDir
$WindowsEvidenceCount = Count-Files $WindowsEvidenceDir "*.txt"
$WindowsLatestEvidence = Latest-File $WindowsEvidenceDir "*.txt"
$AdapterDryRunStatus = Adapter-DryRun

$lines = @(
  "Sherlockdogs doctor",
  "version=$($manifestObj.version)",
  "channel=$($manifestObj.channel)",
  "admin=$(Admin-Status)",
  "process.wechat=$(Process-Status @('WeChat','Weixin'))",
  "project=$ProjectDir status=$(Status-Path $ProjectDir)",
  "manifest=$Manifest status=$(Status-Path $Manifest)",
  "config=$ConfigFile status=$(Status-Path $ConfigFile)",
  "inbox=$InboxDir status=$(Status-Path $InboxDir)",
  "vault=$VaultDir status=$(Status-Path $VaultDir)",
  "clipping=$ClippingDir status=$(Status-Path $ClippingDir)",
  "work=$WorkDir status=$(Status-Path $WorkDir)",
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
  "task.local-inbox.last_result=$(Task-LastResult SherlockdogsLocalInbox)",
  "task.local-inbox.last_run=$(Task-LastRun SherlockdogsLocalInbox)",
  "task.local-inbox.latest_log=$(Latest-File $DiagnosticsDir 'task-local-inbox-*.log')",
  "task.codex-runner=$RunnerTaskState",
  "task.codex-runner.last_result=$(Task-LastResult SherlockdogsCodexRunner)",
  "task.codex-runner.last_run=$(Task-LastRun SherlockdogsCodexRunner)",
  "task.codex-runner.latest_log=$(Latest-File $DiagnosticsDir 'task-codex-runner-*.log')",
  "task.windows-wechat=$WeChatTaskState",
  "task.windows-wechat.last_result=$(Task-LastResult SherlockdogsWindowsWeChatInbox)",
  "task.windows-wechat.last_run=$(Task-LastRun SherlockdogsWindowsWeChatInbox)",
  "task.windows-wechat.latest_log=$(Latest-File $DiagnosticsDir 'task-windows-wechat-*.log')",
  "wechat_decrypt_helper=$WeChatDecryptDir status=$(Status-Path $WeChatDecryptDir)",
  "wechat_decrypt_latest_log=$(Latest-File $DiagnosticsDir 'wechat-decrypt-*.log')",
  "windows_wechat_latest_connect_report=$(Latest-File $DiagnosticsDir 'windows-wechat-connect-*.txt')",
  "windows_wechat_decrypted_dir=$WindowsWeChatDir status=$(Status-Path $WindowsWeChatDir)",
  "windows_wechat_message_dbs=$WeChatDbCount",
  "windows_receiver_file=$ReceiverFile status=$(Status-Path $ReceiverFile)",
  "windows_receiver_chats=$ReceiverChats",
  "windows_adapter_dry_run=$AdapterDryRunStatus",
  "windows_inbox_events=$WindowsInboxEventCount",
  "windows_latest_inbox_event=$(Latest-File $WindowsInboxEventsDir '*.json')",
  "windows_run_events=$WindowsRunEvents status=$(Status-Path $WindowsRunEvents)",
  "windows_evidence_reports=$WindowsEvidenceCount",
  "windows_latest_evidence=$WindowsLatestEvidence",
  "windows_latest_evidence.token_match=$(Evidence-Field $WindowsLatestEvidence 'token_match')",
  "windows_latest_evidence.windows_wechat_db=$(Evidence-Field $WindowsLatestEvidence 'windows_wechat_db')",
  "windows_latest_evidence.codex_card=$(Evidence-Field $WindowsLatestEvidence 'codex_card')",
  "windows_latest_evidence.receiver_chat=$(Evidence-Field $WindowsLatestEvidence 'receiver_chat')",
  "pending=$(Count-Json (Join-Path $WorkDir 'jobs\pending'))",
  "running=$(Count-Json (Join-Path $WorkDir 'jobs\running'))",
  "done=$(Count-Json (Join-Path $WorkDir 'jobs\done'))",
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
  $Advice += "- Windows WeChat self-chat is not connected; run Sherlockdogs Connect WeChat.cmd with Windows WeChat logged in."
} elseif ($WeChatDbCount -eq 0) {
  $Advice += "- Windows WeChat directory has no decrypted message DBs; check the selected directory."
} elseif ($AdapterDryRunStatus -like "warn:*") {
  $Advice += "- Windows WeChat DB is readable but has adapter warnings; run Windows WeChat Smoke and send this Doctor report if no item arrives."
} elseif ($AdapterDryRunStatus -ne "ok") {
  $Advice += "- Windows WeChat DB exists but adapter dry-run failed; run Sherlockdogs Connect WeChat.cmd again and send this Doctor report."
} elseif ($WeChatTaskState -eq "not registered") {
  $Advice += "- Windows WeChat DB directory is configured but watcher task is missing; run Sherlockdogs Connect WeChat.cmd again."
}
if ($ReceiverChats -eq "missing" -or $ReceiverChats -eq "empty") {
  $Advice += "- No Windows receiver chat is saved yet; run Run Windows WeChat Smoke.cmd after forwarding a #2 item to yourself."
}
if ($WindowsEvidenceCount -eq 0) {
  $Advice += "- No Windows WeChat DB smoke evidence report yet; run Collect Windows WeChat Evidence.cmd after Windows WeChat receives the #2 message."
}
if ($FailedCount -ne 0) { $Advice += "- Failed jobs exist; open Diagnostics and send the latest doctor report." }
$lines += "next_steps:"
if ($Advice.Count -eq 0) {
  $lines += "- OK: forward links/files/text from phone WeChat to yourself; Windows WeChat must receive them."
  $lines += "- Optional fallback: drop files or links into $InboxDir."
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
