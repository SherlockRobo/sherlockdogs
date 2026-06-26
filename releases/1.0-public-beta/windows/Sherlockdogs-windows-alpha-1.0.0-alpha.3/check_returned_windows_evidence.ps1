param(
  [Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)]
  [string[]]$Path
)
$ErrorActionPreference = "Stop"

$LatestReport = $null
foreach ($Root in $Path) {
  if (Test-Path $Root -PathType Leaf) {
    $Candidate = Get-Item -Path $Root
  } elseif (Test-Path $Root -PathType Container) {
    $Candidate = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -like "*windows-wechat-db-smoke*.txt" -or
        ($_.DirectoryName -match "[/\\]windows-wechat-db-smoke$")
      } |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1
  } else {
    $Candidate = $null
  }
  if ($Candidate) {
    $LatestReport = $Candidate.FullName
    break
  }
}

if (-not $LatestReport) {
  Write-Host "windows_wechat_db_verified=false"
  Write-Host "windows_wechat_db_evidence=missing"
  exit 1
}

$Text = Get-Content -Raw -Encoding UTF8 -Path $LatestReport
$Required = @(
  "token_match=ok",
  "windows_wechat_db=ok",
  "connect_wechat=ok",
  "self_chat_received=ok",
  "desktop_received=ok",
  "codex_job_created=ok",
  "codex_card=ok",
  "thread_completed=True"
)
foreach ($Needle in $Required) {
  if ($Text -notlike "*$Needle*") {
    Write-Host "windows_wechat_db_verified=false"
    Write-Host "windows_wechat_db_evidence=invalid"
    Write-Host "missing=$Needle"
    Write-Host "report=$LatestReport"
    exit 1
  }
}

Write-Host "windows_wechat_db_verified=true"
Write-Host "windows_wechat_db_evidence=$LatestReport"
