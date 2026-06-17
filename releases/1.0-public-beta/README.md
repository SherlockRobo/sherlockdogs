# Sherlockdogs 1.0 Public Beta

Status: `MAC_READY_WINDOWS_DB_BOOTSTRAP_READY_NEEDS_SMOKE`

This is the small-scope Sherlockdogs 1.0 beta package. macOS is ready for public beta testing. Windows now includes the Mac-like WeChat DB adapter and local decrypt bootstrap, but it still needs a real Windows self-chat smoke before it can carry the same promise.

## Choose Your Platform

| Platform | Folder | First Command |
|---|---|---|
| macOS | [`macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/`](macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/) | `Sherlockdogs Start.app` |
| Windows | [`windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2/`](windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2/) | `Sherlockdogs Start.cmd`, then `Sherlockdogs Connect WeChat.cmd` |

Use the whole platform folder. Open `START_HERE.md` first.

## What You Are Testing

```text
macOS:
  Phone WeChat -> forward to yourself -> local Mac WeChat DB -> Markdown/Codex

Windows target:
  Phone WeChat -> forward to yourself -> local Windows WeChat DB -> Markdown/Codex

Windows current:
  DB adapter, Connect entry, decrypt bootstrap, and evidence collector are packaged.
  Full parity still needs real Windows self-chat + Codex-card smoke evidence.
```

## Install Guides

![Mac install guide](macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/INSTALL_GUIDE_FOR_USERS.png)

## Known Beta Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and depends on local Mac WeChat state.
- Windows is not full public-beta ready until the packaged DB adapter/bootstrap is proven on a real Windows WeChat profile.

## Evidence

| Evidence | Path |
|---|---|
| Public beta decision | [`docs/PUBLIC_BETA_DECISION.json`](docs/PUBLIC_BETA_DECISION.json) |
| Share note | [`docs/SHARE_PUBLIC_BETA.md`](docs/SHARE_PUBLIC_BETA.md) |
| Windows runtime smoke | [`evidence/windows-runtime-smoke/`](evidence/windows-runtime-smoke/) proves Windows runtime packaging, not WeChat DB parity |
| Windows WeChat DB smoke | Pending; required before Windows can be called Mac-parity ready |
| Mobile entry smoke | [`evidence/mobile-entry-smoke/`](evidence/mobile-entry-smoke/) |

## No Archives

This beta intentionally does not publish zip, dmg, tar, or other archive files.
