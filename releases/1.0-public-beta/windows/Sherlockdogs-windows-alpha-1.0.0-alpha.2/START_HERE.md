# Start Here: Sherlockdogs Windows Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Optional: install/sign in to a sync drive such as Nutstore, OneDrive, Google Drive, Syncthing, or NAS.
3. Double-click `Sherlockdogs Start.cmd`.
4. Create the phone share action from `IOS_SHORTCUTS_GUIDE.md`.
   Or import `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` as the beta shortcut seed.
5. Local-only users can stop here; Nutstore users can double-click `Configure Nutstore Inbox.cmd`.
6. Send links/files from your phone to your selected Inbox.
7. Open results with `Open Sherlockdogs Output.cmd`.
8. If anything fails, run `Doctor Sherlockdogs.cmd`.

## What this beta does

- Uses your own local or synced Inbox.
- Saves and processes clippings locally after Nutstore sync.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Does not read your personal WeChat database by default.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `Sherlockdogs Start.cmd` | First install |
| `Configure Nutstore Inbox.cmd` | Optional helper: switch Inbox to your own Nutstore synced folder |
| `Open Sherlockdogs Output.cmd` | View saved Markdown/results |
| `Doctor Sherlockdogs.cmd` | Generate diagnostics |
| `Uninstall Sherlockdogs.cmd` | Remove background tasks |
| `INSTALL_GUIDE_FOR_USERS.png` | User-facing picture guide |
| `INSTALL_GUIDE_FOR_USERS.svg` | Editable picture source |
| `IOS_SHORTCUTS_GUIDE.md` | Phone share action guide |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Importable iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `WINDOWS_PACKAGE_BRIEF.md` | Windows package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, include the latest Doctor output.
