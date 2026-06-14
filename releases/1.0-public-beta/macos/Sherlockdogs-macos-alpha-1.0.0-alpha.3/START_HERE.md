# Start Here: Sherlockdogs Mac Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Optional: install/sign in to a sync drive such as iCloud Drive, Nutstore, OneDrive, Google Drive, Syncthing, or NAS.
3. Double-click `Sherlockdogs Start.app`.
4. Create the phone share action from `IOS_SHORTCUTS_GUIDE.md`.
   Or import `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` as the beta shortcut seed.
5. Local-only users can stop here; Nutstore users can double-click `Configure Nutstore Inbox.command`.
6. Send links/files from your phone to your selected Inbox.
7. Optional, best experience on Mac: double-click `Sherlockdogs Connect WeChat.app`, then forward one test article/link/image to yourself in WeChat.
8. Open results with `Sherlockdogs Open Output.app`.
9. If anything fails, run `Sherlockdogs Doctor.app`.

## What this beta does

- Uses your own local or synced Inbox.
- Saves and processes clippings locally after Nutstore sync.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Does not read your personal WeChat database by default; Mac Personal Mode reads it only after you run `Sherlockdogs Connect WeChat.app`.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `Sherlockdogs Start.app` | First install, preferred on Mac |
| `Configure Nutstore Inbox.command` | Optional helper: switch Inbox to your own Nutstore synced folder |
| `Sherlockdogs Doctor.app` | Generate diagnostics, preferred on Mac |
| `Sherlockdogs Connect WeChat.app` | Optional Mac Personal Mode: bind your own WeChat self-chat |
| `Sherlockdogs Open Output.app` | View saved Markdown/results, preferred on Mac |
| `Uninstall Sherlockdogs.command` | Remove background services |
| `INSTALL_GUIDE_FOR_USERS.png` | User-facing picture guide |
| `INSTALL_GUIDE_FOR_USERS.svg` | Editable picture source |
| `IOS_SHORTCUTS_GUIDE.md` | Phone share action guide |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Importable iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `MAC_PACKAGE_BRIEF.md` | Mac package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, include the latest Doctor output.

## If macOS blocks the app

This alpha uses local ad-hoc signing, not App Store notarization. If macOS blocks the first open, right-click `Sherlockdogs Start.app`, choose Open, then confirm Open.
If that still fails, run this in Terminal from the package folder: `xattr -dr com.apple.quarantine . && chmod +x "Configure Nutstore Inbox.command" "Uninstall Sherlockdogs.command"`.
