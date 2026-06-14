# Sherlockdogs 1.0 Public Beta

Status: READY_FOR_PUBLIC_BETA

This folder contains the public beta release folders for Sherlockdogs 1.0.

## Download / Use

Use the whole platform folder as-is. Do not copy only the top-level launcher.

| Platform | Folder |
|---|---|
| macOS | `macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/` |
| Windows | `windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2/` |

## Start

| Platform | First step |
|---|---|
| macOS | Open `START_HERE.md`, then double-click `Sherlockdogs Start.app` |
| Windows | Open `START_HERE.md`, then double-click `Sherlockdogs Start.cmd` |

## Beta Boundary

The stable core path is:

```text
Start Sherlockdogs -> send content to Sherlockdogs Inbox -> open output
```

Mac WeChat Personal Mode is optional. It is verified on the maintainer machine, but it depends on local Mac WeChat state and should not be treated as the only entry point.

## Evidence

Readiness evidence lives in `docs/` and `evidence/`.

| Evidence | Path |
|---|---|
| Decision | `docs/PUBLIC_BETA_DECISION.json` |
| Share note | `docs/SHARE_PUBLIC_BETA.md` |
| Windows runtime smoke | `evidence/windows-runtime-smoke/` |
| Mobile entry smoke | `evidence/mobile-entry-smoke/` |

## No Archives

This release intentionally does not provide zip, dmg, tar, or other archive files.
