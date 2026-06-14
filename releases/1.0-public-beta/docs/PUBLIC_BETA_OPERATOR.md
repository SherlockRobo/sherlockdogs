# Sherlockdogs Public Beta Operator Guide

## Goal

Build Mac and Windows public beta folders without manual judgement in the middle.

## One Command

```bash
packaging/public_beta_auto.sh
```

The auto command chooses the best available path:

- existing GitHub repo -> trigger Windows runner and import evidence
- bootstrap enabled -> create/update a private smoke repo and import evidence
- no GitHub path -> run local gates and report the missing Windows evidence

Core local gate:

```bash
packaging/public_beta_go.sh
```

Optional: pass a returned Windows folder, report folder, or report file:

```bash
packaging/public_beta_go.sh /path/to/windows-returned-folder-or-evidence
```

Optional: import the latest successful GitHub Actions artifact first:

```bash
SHERLOCKDOGS_IMPORT_GITHUB_EVIDENCE=1 packaging/public_beta_go.sh
```

Optional: trigger GitHub Actions, wait for Windows evidence, import it, then run the full gate:

```bash
SHERLOCKDOGS_GITHUB_REPO=owner/repo SHERLOCKDOGS_GITHUB_TRIGGER_WINDOWS=1 packaging/public_beta_go.sh
```

Optional: create or update a dedicated private GitHub smoke repo, then run the full Windows evidence loop:

```bash
SHERLOCKDOGS_GITHUB_BOOTSTRAP_EXECUTE=1 packaging/public_beta_auto.sh
```

Dry-run first:

```bash
packaging/public_beta_github_bootstrap.sh
```

The command imports Windows runtime evidence, rebuilds both release folders, runs all gates, and writes the final decision to:

```text
dist/PUBLIC_BETA_DECISION.md
dist/PUBLIC_BETA_DECISION.json
```

Quick status without rebuilding:

```bash
packaging/public_beta_status.sh
```

GitHub Windows runner preflight without triggering a run:

```bash
SHERLOCKDOGS_GITHUB_REPO=owner/repo packaging/public_beta_github_preflight.sh
```

GitHub auth can come from either:

- `gh auth login`
- `GH_TOKEN` with repo/workflow permissions

If GitHub rejects updates to `.github/workflows/windows-runtime-smoke.yml`, refresh the CLI token:

```bash
gh auth refresh -h github.com -s workflow
```

Hard gate for publish scripts:

```bash
packaging/public_beta_require_ready.sh
```

It exits non-zero unless `dist/PUBLIC_BETA_DECISION.json` says `READY_FOR_PUBLIC_BETA`.

## Decision States

| Decision | Meaning |
|---|---|
| `READY_FOR_PUBLIC_BETA` | Mac, Windows runtime, and phone entry are verified |
| `NEEDS_WINDOWS_RUNTIME_SMOKE` | Mac is ready and Windows package is assembled, but Windows runtime evidence is missing |
| `NEEDS_MOBILE_ENTRY_SMOKE` | Desktop packages are ready, but phone-to-desktop entry evidence is missing |

## Windows Evidence

Valid Windows runtime evidence must include all four lines:

```text
runtime_smoke=ok
preflight=ok
selftest=ok
doctor=ok
```

Evidence can come from any of these places:

| Source | Path |
|---|---|
| Windows release folder | `dist/windows-beta/Sherlockdogs-windows-alpha-1.0.0-alpha.2/evidence/windows-runtime-smoke/` |
| Central evidence folder | `dist/evidence/windows-runtime-smoke/` |
| GitHub Actions artifact | `sherlockdogs-windows-runtime-smoke` |
| External returned folder | pass it to `packaging/public_beta_go.sh <path>` |

Manual GitHub artifact import:

```bash
packaging/import_github_windows_runtime_evidence.sh
```

Or pass a specific run id:

```bash
packaging/import_github_windows_runtime_evidence.sh <run-id>
```

One-command GitHub evidence run:

```bash
SHERLOCKDOGS_GITHUB_REPO=owner/repo packaging/import_github_windows_runtime_evidence.sh --trigger --wait
```

Use `owner/repo` for the GitHub repository that contains `.github/workflows/windows-runtime-smoke.yml`.
Run `packaging/public_beta_github_preflight.sh` first if the one-command run fails.

If there is no repo yet, use `packaging/public_beta_github_bootstrap.sh`. It creates a dedicated smoke repo only when `SHERLOCKDOGS_GITHUB_BOOTSTRAP_EXECUTE=1` is set.

## GitHub Actions

The workflow is already installed at:

```text
.github/workflows/windows-runtime-smoke.yml
```

It runs the Windows runtime smoke on `windows-latest` and uploads:

```text
evidence/windows-runtime-smoke/**
```

as the artifact:

```text
sherlockdogs-windows-runtime-smoke
```

## Release Folders

| Platform | Folder |
|---|---|
| macOS | `dist/macos-beta/Sherlockdogs-macos-alpha-1.0.0-alpha.3` |
| Windows | `dist/windows-beta/Sherlockdogs-windows-alpha-1.0.0-alpha.2` |

Share the whole folder as-is. Do not create zip, dmg, tar, or other archive files.

## Verification Gates

`packaging/public_beta_go.sh` covers:

- Mac release gate and smoke test
- Windows static release gate
- Windows runtime evidence import
- Optional GitHub Actions artifact evidence import
- Windows runtime evidence preservation across rebuilds
- READY and PENDING decision paths
- JSON decision and hard READY gate
- No cache files or archive files in `dist/`

## Current Boundary

The default public beta uses the tester's own local or synced Inbox. Sherlockdogs only watches that local folder. The sync provider can be iCloud Drive, Nutstore, OneDrive, Google Drive, Syncthing, NAS, or a plain local folder. It does not read personal WeChat databases and does not upload clipping content to a Sherlockdogs relay service by default.

Sherlockdogs 1.0 is not public-beta ready unless a real phone entry is verified. Desktop drag/drop and local sample files are useful smoke tests, but they do not satisfy the 1.0 product promise. After sending one real `#2` item from phone WeChat to the user's own WeChat, generate evidence with:

```bash
python3 scripts/collect_mobile_entry_evidence.py --write
packaging/release_check_all.sh
```

The evidence report is written into `dist/evidence/mobile-entry-smoke/` and must include:

```text
mobile_entry=ok
desktop_received=ok
codex_card=ok
```
