param([switch]$SkipDoctor)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$ConfigFile = Join-Path $env:USERPROFILE ".sherlockdogs\config.ps1"
if (Test-Path $ConfigFile) { . $ConfigFile }

$DoctorScript = Join-Path $PSScriptRoot "doctor.ps1"
$EvidenceDir = Join-Path $ProjectDir "evidence\windows-wechat-db-smoke"
$DiagnosticsDir = Join-Path $env:USERPROFILE ".sherlockdogs\diagnostics"
$ExportRoot = Join-Path ([Environment]::GetFolderPath("Desktop")) ("Sherlockdogs-Windows-Evidence-{0}" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

function Latest-File($path, $filter) {
  if (-not (Test-Path $path)) { return $null }
  return Get-ChildItem -Path $path -Filter $filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function Copy-IfExists($path, $targetDir) {
  if ($path -and (Test-Path $path)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
    Copy-Item -Force -Path $path -Destination $targetDir
    return (Join-Path $targetDir (Split-Path $path -Leaf))
  }
  return ""
}

function Copy-LatestFiles($path, $filter, $targetDir, $count) {
  if (-not (Test-Path $path)) { return @() }
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  $copied = @()
  $files = @(Get-ChildItem -Path $path -Filter $filter -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First $count)
  foreach ($file in $files) {
    Copy-Item -Force -Path $file.FullName -Destination $targetDir
    $copied += (Join-Path $targetDir $file.Name)
  }
  return $copied
}

New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null

if (-not $SkipDoctor -and (Test-Path $DoctorScript)) {
  try {
    & $DoctorScript -Report | Tee-Object -FilePath (Join-Path $ExportRoot "doctor-run-output.txt") | Out-Null
  } catch {
    "Doctor failed: $($_.Exception.Message)" | Set-Content -Encoding UTF8 (Join-Path $ExportRoot "doctor-run-error.txt")
  }
}

$LatestEvidence = Latest-File $EvidenceDir "*.txt"
$LatestDoctor = Latest-File $DiagnosticsDir "doctor-*.txt"
$LatestConnectReport = Latest-File $DiagnosticsDir "windows-wechat-connect-*.txt"
$LatestDecryptLog = Latest-File $DiagnosticsDir "wechat-decrypt-*.log"

$CopiedEvidence = Copy-IfExists $LatestEvidence.FullName (Join-Path $ExportRoot "windows-wechat-db-smoke")
$CopiedDoctor = Copy-IfExists $LatestDoctor.FullName (Join-Path $ExportRoot "diagnostics")
$CopiedConnectReport = Copy-IfExists $LatestConnectReport.FullName (Join-Path $ExportRoot "diagnostics")
$CopiedDecryptLog = Copy-IfExists $LatestDecryptLog.FullName (Join-Path $ExportRoot "diagnostics")
$CopiedTaskLogs = Copy-LatestFiles $DiagnosticsDir "task-*.log" (Join-Path $ExportRoot "diagnostics") 5

$summary = @(
  "Sherlockdogs Windows evidence export",
  "created_at=$(Get-Date -Format o)",
  "project=$ProjectDir",
  "export_dir=$ExportRoot",
  "latest_evidence=$($LatestEvidence.FullName)",
  "copied_evidence=$CopiedEvidence",
  "latest_doctor=$($LatestDoctor.FullName)",
  "copied_doctor=$CopiedDoctor",
  "latest_connect_report=$($LatestConnectReport.FullName)",
  "copied_connect_report=$CopiedConnectReport",
  "latest_decrypt_log=$($LatestDecryptLog.FullName)",
  "copied_decrypt_log=$CopiedDecryptLog",
  "copied_task_logs=$($CopiedTaskLogs -join ';')",
  "",
  "Send this whole folder back to the operator. Do not zip it unless the operator explicitly asks for an archive.",
  "Passing Windows parity still requires token_match=ok, windows_wechat_db=ok, codex_job_created=ok, codex_card=ok, and thread_completed=True in the evidence report."
)
$summary | Set-Content -Encoding UTF8 (Join-Path $ExportRoot "README_SEND_THIS_FOLDER.txt")

Write-Host "evidence_export=$ExportRoot"
if (-not $CopiedEvidence) { Write-Host "warning=no windows-wechat-db-smoke report found yet" }
if (-not $CopiedDoctor) { Write-Host "warning=no doctor report found yet" }
