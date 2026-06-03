# Architecture

Sherlockdogs is organized around a small local pipeline.

```text
adapter -> parser -> router -> archive writer -> task writer -> Codex handoff
```

## Adapter

Adapters convert local sources into plain text payloads.

Examples:

- manual paste
- watched text file
- clipboard
- browser share extension
- local chat export

Private app database adapters are intentionally kept outside the public quickstart.

## Parser

The parser extracts:

- URLs
- command level
- source type
- title hints
- raw context

## Router

The router maps commands to behavior:

| Level | Behavior |
|---|---|
| 1 | Archive only |
| 2 | Archive + Codex card |
| 3 | Lightweight parsing |
| 4 | Deep reading |
| 5 | Heavy media processing |

## Archive Writer

Writes Markdown and JSON metadata under:

```text
<vault>/clipping/<source>/<slug>/
```

## Task Writer

Writes Codex-ready JSON jobs under:

```text
<vault>/jobs/pending/
```

The current OSS runner stops at job creation. Production dogfood builds connect those jobs to Codex sessions.

