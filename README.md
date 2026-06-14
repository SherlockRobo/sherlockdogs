# Sherlockdogs

Local-first AI clue pipeline: forward anything, keep a private Markdown memory layer, and turn selected items into Codex-ready tasks.

Sherlockdogs is not an Obsidian plugin. It treats Markdown/Obsidian as the private library, and Codex as the working interface. The current project is under intensive dogfooding in a real production workflow before broader community adoption.

## What It Does

- Accepts links, text, images, and media references from local inboxes.
- Routes each item by command level, from archive-only to deep Codex processing.
- Writes auditable Markdown artifacts for later retrieval.
- Creates compact Codex task payloads for items that need AI work.
- Keeps user data local by default.

## Command Levels

| Command | Behavior |
|---|---|
| no tag or `#1` | Save locally only |
| `#` or `#2` | Save locally and create a Codex card |
| `#3` | Prepare lightweight metadata/transcript analysis |
| `#4` or `#ob` | Prepare deep reading / distillation |
| `#5` | Prepare heavier media breakdown tasks |

## Architecture

```text
Input inbox
  -> Sherlockdogs parser
  -> job queue
  -> local Markdown archive
  -> optional Codex task
```

The production dogfood build currently uses personal local inbox adapters. This open-source repository starts with a safe text/file adapter so new users can run it without touching private app databases.

## Quickstart

## Public Beta

Small-scope 1.0 public beta folders are available at:

```text
releases/1.0-public-beta/
```

Use the whole macOS or Windows folder as-is. No zip/dmg/tar package is published.

Mac WeChat Personal Mode is optional; the stable beta entry is local or synced Inbox.

## Developer Quickstart

```bash
git clone https://github.com/SherlockRobo/sherlockdogs.git
cd sherlockdogs
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sdogs ingest "https://example.com/article #2" --vault ./demo-vault
```

Output:

```text
demo-vault/clipping/web/<slug>/raw.md
demo-vault/clipping/web/<slug>/metadata.json
demo-vault/jobs/pending/<job-id>.json
```

## Examples

See `examples/` for real workflow shapes:

- WeChat article clipping.
- X / social post capture.
- Video link preflight.
- Mixed text + link bundle.

The examples are anonymized and contain no private chat logs, tokens, cookies, or local database paths.

## Privacy

Sherlockdogs is designed for local-first workflows:

- No hosted inbox is required.
- No third-party bot account is required for the default OSS path.
- Raw archives stay in your chosen local vault directory.
- Credentials, cookies, and private app databases are intentionally excluded from this repository.

## Status

Early OSS extraction from a working dogfood system.

Current focus:

- Stable local ingestion.
- Better examples and docs.
- Windows package design.
- Media preflight for XHS, Bilibili, YouTube, TikTok, and Douyin.
- Codex task handoff quality.
