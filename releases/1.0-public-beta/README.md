# Sherlockdogs 1.0 Public Beta

Status: `MAC_READY_WINDOWS_DB_NOT_READY`

This is the small-scope macOS public beta package for Sherlockdogs 1.0. Windows is not ready for the same product promise yet.

## Choose Your Platform

| Platform | Folder | First Command |
|---|---|---|
| macOS | [`macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/`](macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/) | `Sherlockdogs Start.app` |
| Windows | Not ready | Windows WeChat DB adapter pending |

Use the whole macOS folder. Open `START_HERE.md` first.

## What You Are Testing

```text
macOS:
  Phone WeChat -> forward to yourself -> local Mac WeChat DB -> Markdown/Codex

Windows target:
  Phone WeChat -> forward to yourself -> local Windows WeChat DB -> Markdown/Codex

Windows current:
  Not ready. The existing Windows folder is only an Inbox/Shortcut experiment.
```

## Install Guides

![Mac install guide](macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/INSTALL_GUIDE_FOR_USERS.png)

## Known Beta Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and depends on local Mac WeChat state.
- Windows is not public-beta ready because it does not read Windows WeChat DB or capture WeChat self-chat like macOS.

## Evidence

| Evidence | Path |
|---|---|
| Public beta decision | [`docs/PUBLIC_BETA_DECISION.json`](docs/PUBLIC_BETA_DECISION.json) |
| Share note | [`docs/SHARE_PUBLIC_BETA.md`](docs/SHARE_PUBLIC_BETA.md) |
| Windows runtime smoke | [`evidence/windows-runtime-smoke/`](evidence/windows-runtime-smoke/) only proves the old Inbox runtime, not WeChat DB parity |
| Mobile entry smoke | [`evidence/mobile-entry-smoke/`](evidence/mobile-entry-smoke/) |

## No Archives

This beta intentionally does not publish zip, dmg, tar, or other archive files.
