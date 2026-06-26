param([switch]$NoCodex)
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }

$DiagnosticsDir = Join-Path $env:USERPROFILE ".sherlockdogs\diagnostics"
$ExportScript = Join-Path $PSScriptRoot "export_windows_evidence.ps1"
$DoctorScript = Join-Path $PSScriptRoot "doctor.ps1"
$Codex = if ($env:CODEX_BIN) { $env:CODEX_BIN } else { (Get-Command codex -ErrorAction SilentlyContinue).Source }
$ClippingDir = if ($env:SHERLOCKDOGS_CLIPPING_DIR) { $env:SHERLOCKDOGS_CLIPPING_DIR } else { Join-Path $env:USERPROFILE "Sherlockdogs\Vault\clipping" }
$WorkDir = if ($env:SHERLOCKDOGS_WORK_DIR) { $env:SHERLOCKDOGS_WORK_DIR } else { Join-Path $ClippingDir "_sherlockdogs" }

New-Item -ItemType Directory -Force -Path $DiagnosticsDir | Out-Null

function Write-Utf8NoBomText([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Latest-File($Path, $Filter) {
  if (-not (Test-Path $Path)) { return $null }
  return Get-ChildItem -Path $Path -Filter $Filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function Latest-Dir($Path, $Filter) {
  if (-not (Test-Path $Path)) { return $null }
  return Get-ChildItem -Path $Path -Filter $Filter -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

Write-Host "Sherlockdogs OneClick Codex Help"
Write-Host "project=$ProjectDir"
Write-Host "work=$WorkDir"

$ExportLog = Join-Path $DiagnosticsDir ("oneclick-export-{0}.log" -f (Get-Date -Format yyyyMMdd-HHmmss))
$ExportOutput = @()
if (Test-Path $ExportScript) {
  $ExportOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $ExportScript 2>&1
  $ExportOutput | Set-Content -Encoding UTF8 $ExportLog
  Write-Host ($ExportOutput | Out-String)
} elseif (Test-Path $DoctorScript) {
  $ExportOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $DoctorScript -Report 2>&1
  $ExportOutput | Set-Content -Encoding UTF8 $ExportLog
  Write-Host ($ExportOutput | Out-String)
} else {
  "No export or doctor script found." | Set-Content -Encoding UTF8 $ExportLog
}

$EvidenceDir = ""
$ExportLine = $ExportOutput | Where-Object { $_ -match '^evidence_export=' } | Select-Object -First 1
if ($ExportLine) {
  $EvidenceDir = ($ExportLine -replace '^evidence_export=', '').Trim()
}
if (-not $EvidenceDir -or -not (Test-Path $EvidenceDir)) {
  $LatestEvidenceDir = Latest-Dir ([Environment]::GetFolderPath("Desktop")) "Sherlockdogs-Windows-Evidence-*"
  if ($LatestEvidenceDir) { $EvidenceDir = $LatestEvidenceDir.FullName }
}

$LatestDoctor = Latest-File $DiagnosticsDir "doctor-*.txt"
$LatestConnect = Latest-File $DiagnosticsDir "windows-wechat-connect-*.txt"
$LatestDecrypt = Latest-File $DiagnosticsDir "wechat-decrypt-*.log"
$LatestTask = Latest-File $DiagnosticsDir "task-windows-wechat-*.log"

$PromptPath = Join-Path $DiagnosticsDir ("codex-help-prompt-{0}.md" -f (Get-Date -Format yyyyMMdd-HHmmss))
$FinalPath = Join-Path $DiagnosticsDir ("codex-help-final-{0}.md" -f (Get-Date -Format yyyyMMdd-HHmmss))
$CodexLog = Join-Path $DiagnosticsDir ("codex-help-run-{0}.log" -f (Get-Date -Format yyyyMMdd-HHmmss))

$Prompt = @"
You are Codex repairing Sherlockdogs Windows public beta on this user's machine.

Goal:
Make this path work end to end:
phone WeChat -> Windows desktop WeChat local DB -> decrypted DB -> Sherlockdogs jobs -> Codex task -> Obsidian clipping folder.

Start by reading these local artifacts:
- Evidence folder: $EvidenceDir
- Doctor report: $($LatestDoctor.FullName)
- Connect report: $($LatestConnect.FullName)
- WeChat decrypt log: $($LatestDecrypt.FullName)
- Windows WeChat task log: $($LatestTask.FullName)
- Config file: $ConfigFile
- Project folder: $ProjectDir
- Work folder: $WorkDir
- Clipping folder: $ClippingDir

Known failure points to check first:
1. WeChat DB decrypt helper or vxcli is missing, stale, or cannot decrypt the current WeChat version.
2. The decrypted DB is stale; each windows-wechat task run must perform incremental decrypt before polling.
3. The receiver file may contain BOM or the wrong chat id/name.
4. The queue and runs must live under SHERLOCKDOGS_WORK_DIR, usually clipping/_sherlockdogs.
5. Scheduled Tasks should use hidden_task_runner.vbs so the desktop does not flash PowerShell windows.
6. Codex may be configured as codex.cmd; do not assume a macOS Codex path.

Allowed low-risk fixes:
- Re-run Doctor, Start, Connect, task_runner, and evidence commands.
- Repair config.ps1 paths.
- Recreate Scheduled Tasks for Sherlockdogs.
- Reinstall Python packages inside the Sherlockdogs venv.
- Run the local WeChat decrypt helper incrementally.
- Rewrite the receiver file as UTF-8 without BOM.

Do not delete user files, WeChat DB files, vault contents, keys, or evidence.
Do not zip anything unless the user explicitly asks.
If a key/account authorization or admin permission is required, stop and say exactly what the user must click.

Final answer must be in Chinese with:
【核心结论】
【已检查】
【已修复】
【还需要用户做什么】
"@
Write-Utf8NoBomText $PromptPath $Prompt

Write-Host "prompt=$PromptPath"
if ($EvidenceDir -and (Test-Path $EvidenceDir)) {
  Copy-Item -Force -Path $PromptPath -Destination (Join-Path $EvidenceDir "codex-help-prompt.md")
  Write-Host "evidence=$EvidenceDir"
  Start-Process explorer.exe $EvidenceDir
}

if ($NoCodex -or -not $Codex) {
  Write-Host "Codex CLI not found or skipped. Opening the prompt file."
  Start-Process notepad.exe $PromptPath
  exit 2
}

Write-Host "codex=$Codex"
Write-Host "Starting Codex repair task..."
$CodexArgs = @(
  "exec",
  "--cd", $ProjectDir,
  "--dangerously-bypass-approvals-and-sandbox",
  "--skip-git-repo-check",
  "--output-last-message", $FinalPath,
  "-"
)

$PromptText = Get-Content -Raw -Encoding UTF8 $PromptPath
$CodexOutput = $PromptText | & $Codex @CodexArgs 2>&1
$ExitCode = $LASTEXITCODE
$CodexOutput | Set-Content -Encoding UTF8 $CodexLog
Write-Host ($CodexOutput | Out-String)
Write-Host "codex_log=$CodexLog"
Write-Host "codex_final=$FinalPath"
exit $ExitCode
