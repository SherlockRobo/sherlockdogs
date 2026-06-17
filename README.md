# Sherlockdogs

Forward to yourself. Turn phone finds into local Markdown and Codex tasks.

![Sherlockdogs hero](docs/assets/sherlockdogs-hero.png)

Sherlockdogs is a local-first clipping pipeline for people who collect ideas on a phone but work in Markdown, Obsidian, and Codex on a desktop.

The main beta path is intentionally simple:

```text
phone WeChat self-chat
-> desktop WeChat receives it
-> Sherlockdogs reads the local desktop WeChat DB after opt-in setup
-> local Markdown archive
-> optional Codex task
```

Obsidian is a recommended reader for the Markdown library, but it is not required.

## Public Beta

Status: `READY_FOR_PUBLIC_BETA`

| Platform | Beta folder | Current status |
|---|---|---|
| macOS | [Sherlockdogs-macos-alpha-1.0.0-alpha.3](releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/) | Real self-chat -> local WeChat DB -> Markdown/Codex smoke passed |
| Windows | [Sherlockdogs-windows-alpha-1.0.0-alpha.2](releases/1.0-public-beta/windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2/) | Same product path is packaged; waiting for first real Windows self-chat smoke |
| iOS Shortcut / Inbox | Included as fallback | Optional fallback when local DB path is not usable |

No zip, dmg, tar, or installer archive is published for this beta. Use the whole platform folder as-is.

## Quick Start

![Quickstart flow](docs/assets/quickstart-flow.png)

| Step | macOS | Windows |
|---|---|---|
| 1 | Open the macOS beta folder | Open the Windows beta folder |
| 2 | Read `START_HERE.md` | Read `START_HERE.md` |
| 3 | Open `Sherlockdogs Start.app` | Run `Sherlockdogs Start.cmd` |
| 4 | Optional best path: `Sherlockdogs Connect WeChat.app` | Run `Sherlockdogs Connect WeChat.cmd` or `Run Windows WeChat Smoke.cmd` |
| 5 | Forward an item to yourself in WeChat | Forward an item to yourself in WeChat |
| 6 | Open output with `Sherlockdogs Open Output.app` | Open output with `Open Sherlockdogs Output.cmd` |

First launch may spend a few minutes installing Python dependencies. macOS may require right-click -> Open on the first launch.

## What It Does

- Captures links, text, media references, and WeChat self-chat entries into a local archive.
- Writes `raw.md`, `metadata.json`, README-style notes, and result folders.
- Creates Codex-ready tasks when an item is marked with `#` or `#2`.
- Keeps raw content in the user's local vault by default.
- Supports Obsidian as a reader without making it a hard dependency.
- Keeps iOS Shortcut / Inbox / sync-folder capture as a fallback, not the main public-beta path.

## Command Levels

| Command | Behavior |
|---|---|
| no tag or `#1` | Save locally only |
| `#` or `#2` | Save locally and create a Codex card |
| `#3` | Prepare lightweight metadata/transcript analysis |
| `#4` or `#ob` | Prepare deep reading / distillation |
| `#5` | Prepare heavier media breakdown tasks |

## Windows Feedback Loop

Windows is packaged for the same user path as macOS:

```text
phone WeChat -> self-chat -> desktop WeChat DB -> Markdown/Codex
```

The beta still needs real Windows machine evidence before it should be described as fully equivalent to macOS. If Windows fails, run:

```text
Export Windows Evidence.cmd
```

Then send back the generated `Sherlockdogs-Windows-Evidence-*` folder. It helps identify whether the problem is DB discovery, key/decrypt, self-chat receive, task creation, or Codex handoff.

## Privacy Boundary

Sherlockdogs is designed for local-first workflows:

- No hosted inbox is required.
- No third-party bot account is required for the main path.
- Raw archives stay in your local vault.
- Private app databases, credentials, and cookies are excluded from this public repository.
- WeChat DB access is opt-in and local. If it does not work on a machine, use the iOS Shortcut / Inbox fallback.

## Developer Quickstart

The open-source CLI can be tested without WeChat, Obsidian, or Codex:

```bash
git clone https://github.com/SherlockRobo/sherlockdogs.git
cd sherlockdogs
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
sdogs ingest "https://example.com/article #2" --vault ./demo-vault
```

Expected output:

```text
demo-vault/clipping/web/<slug>/raw.md
demo-vault/clipping/web/<slug>/metadata.json
demo-vault/jobs/pending/<job-id>.json
```

See [QUICKSTART.md](QUICKSTART.md) and [docs/architecture.md](docs/architecture.md) for the OSS adapter architecture.

## Release

- Public beta overview: [releases/1.0-public-beta/README.md](releases/1.0-public-beta/README.md)
- Release notes: [releases/1.0-public-beta/RELEASE_NOTES.md](releases/1.0-public-beta/RELEASE_NOTES.md)
- Evidence plan: [docs/evidence-plan.md](docs/evidence-plan.md)
