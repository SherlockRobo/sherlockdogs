# Quickstart

This quickstart runs the safe local text adapter. It does not require WeChat, Obsidian, or Codex.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run One Ingest

```bash
sdogs ingest "https://example.com/research-note #2" --vault ./demo-vault
```

## Inspect Output

```bash
find ./demo-vault -maxdepth 4 -type f | sort
```

Expected files:

```text
demo-vault/clipping/web/<slug>/raw.md
demo-vault/clipping/web/<slug>/metadata.json
demo-vault/jobs/pending/<job-id>.json
```

## Command Levels

```bash
sdogs ingest "https://example.com/save-only" --vault ./demo-vault
sdogs ingest "https://example.com/card #" --vault ./demo-vault
sdogs ingest "https://example.com/deep #4" --vault ./demo-vault
```

## Local Inbox File

Create `inbox.txt`:

```text
Interesting research note
https://example.com/paper
#2
```

Run:

```bash
sdogs ingest-file inbox.txt --vault ./demo-vault
```

## What To Connect Next

The safe OSS adapter can be replaced by platform adapters:

- clipboard watcher
- browser share extension
- local app inbox
- chat export file
- manually pasted text

Keep private app database access and credentials outside the public repository.

