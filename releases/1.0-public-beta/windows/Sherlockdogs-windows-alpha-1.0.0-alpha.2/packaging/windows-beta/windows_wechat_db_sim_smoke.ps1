param(
  [string]$EvidenceDir = "evidence\windows-wechat-db-sim-smoke"
)
$ErrorActionPreference = "Stop"

$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$SmokeHome = Join-Path ([System.IO.Path]::GetTempPath()) ("sherlockdogs-win-db-smoke-" + [System.Guid]::NewGuid().ToString("N"))
$env:USERPROFILE = $SmokeHome
$env:HOME = $SmokeHome
$DbRoot = Join-Path $SmokeHome "wechat-db"
$MessageDir = Join-Path $DbRoot "message"
New-Item -ItemType Directory -Force -Path $SmokeHome, $MessageDir | Out-Null

$Python = (Get-Command python -ErrorAction Stop).Source
$DbPath = Join-Path $MessageDir "message_0.db"
$CreateDb = @'
import sqlite3
import sys
import time

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
conn.execute("create table Msg_wxid_real_self(create_time integer, message_content text, local_type integer)")
conn.execute(
    "insert into Msg_wxid_real_self values (?, ?, ?)",
    (int(time.time()), "https://example.com/windows-ci-wechat-db-sim\n#2", 1),
)
conn.commit()
conn.close()
'@
$CreateDb | & $Python - $DbPath

& (Join-Path $ProjectDir "packaging\windows-beta\install.ps1") -NoTasks -SkipDeps
if ($LASTEXITCODE -ne 0) { throw "install.ps1 failed" }

& (Join-Path $ProjectDir "packaging\windows-beta\connect_wechat.ps1") -DecryptedDbDir $DbRoot -Receivers "*" -NoTask -NoDecryptBootstrap
if ($LASTEXITCODE -ne 0) { throw "connect_wechat.ps1 failed" }

& $env:PYTHON_BIN (Join-Path $ProjectDir "scripts\windows_wechat_inbox.py") --once --db-root $DbRoot --receivers "*" --settle-seconds 0
if ($LASTEXITCODE -ne 0) { throw "windows_wechat_inbox.py failed" }

$CompleteJob = @'
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

project = Path(sys.argv[1])
article_dir = project / "clipping" / "windows-smoke-article"
run_dir = project / "runs" / "windows-smoke-codex-card"
article_dir.mkdir(parents=True, exist_ok=True)
run_dir.mkdir(parents=True, exist_ok=True)
raw_path = article_dir / "raw.md"
readme_path = article_dir / "README.md"
prompt_path = run_dir / "prompt.md"
raw_path.write_text("windows smoke raw\n", encoding="utf-8")
readme_path.write_text("# windows smoke\n", encoding="utf-8")
prompt_path.write_text("windows smoke codex card\n", encoding="utf-8")
done_dir = project / "jobs" / "done"
done_dir.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
for path in sorted((project / "jobs" / "pending").glob("*.json")):
    job = json.loads(path.read_text(encoding="utf-8"))
    job["status"] = "done"
    job["updated_at"] = now
    job["result"] = {
        "ok": True,
        "mode": "clip_card",
        "task_level": 2,
        "capture": {
            "ok": True,
            "article_dir": str(article_dir),
            "raw_path": str(raw_path),
            "readme_path": str(readme_path),
            "asset_count": 0,
        },
        "thread": {
            "ok": True,
            "completed": True,
            "thread_id": "simulated-windows-thread",
            "thread_name": "windows smoke",
            "thread_path": str(run_dir),
            "prompt_path": str(prompt_path),
        },
    }
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.move(str(path), str(done_dir / path.name))
'@
$CompleteJob | & $env:PYTHON_BIN - $ProjectDir

$ResolvedEvidenceDir = Join-Path $ProjectDir $EvidenceDir
New-Item -ItemType Directory -Force -Path $ResolvedEvidenceDir | Out-Null
$EvidenceOutput = & $env:PYTHON_BIN (Join-Path $ProjectDir "scripts\collect_windows_wechat_db_evidence.py") --project-dir $ProjectDir --write --out-dir $ResolvedEvidenceDir
$EvidenceOutput | ForEach-Object { Write-Host $_ }
if ($LASTEXITCODE -ne 0) { throw "collect_windows_wechat_db_evidence.py did not produce a PASS report" }

$Required = @(
  "windows_wechat_db=ok",
  "connect_wechat=ok",
  "self_chat_received=ok",
  "desktop_received=ok",
  "codex_job_created=ok",
  "codex_card=ok",
  "windows_completed_codex_jobs=1",
  "thread_completed=True",
  "receiver_chat=Msg_wxid_real_self"
)
$Joined = ($EvidenceOutput | Out-String)
foreach ($Line in $Required) {
  if ($Joined -notmatch [regex]::Escape($Line)) {
    throw "Missing required evidence line: $Line"
  }
}

Write-Host "windows_wechat_db_sim_smoke=ok"
