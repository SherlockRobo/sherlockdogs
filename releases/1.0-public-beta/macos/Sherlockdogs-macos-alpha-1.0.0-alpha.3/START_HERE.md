# Start Here: Sherlockdogs Mac Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Make sure Mac WeChat is signed in if you want the recommended WeChat path.
3. Double-click `Sherlockdogs Start.app`.
4. Double-click `Sherlockdogs Connect WeChat.app`, then forward one test article/link/image to yourself in WeChat.
5. Open results with `Sherlockdogs Open Output.app`.
6. If anything fails, run `Sherlockdogs Doctor.app`.
7. If a sent item does not arrive, run `Sherlockdogs OneTouchRepair.app`.

## What this beta does

- Uses Mac WeChat self-chat as the recommended path, with Inbox/Shortcut as optional fallback.
- Saves and processes clippings locally after Mac WeChat receives the self-chat item and the local adapter reads it.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Does not read your personal WeChat database by default; Mac Personal Mode reads it only after you run `Sherlockdogs Connect WeChat.app`.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `Sherlockdogs Start.app` | First install, preferred on Mac |
| `Configure Nutstore Inbox.command` | Optional fallback: switch Inbox to your own synced folder |
| `Sherlockdogs Doctor.app` | Generate diagnostics, preferred on Mac |
| `Sherlockdogs OneTouchRepair.app` | One-click fix: enable/restart services, repair WeChat binding, and run one catch-up scan |
| `Sherlockdogs Repair.app` | Restart services, repair WeChat binding, and run one catch-up scan |
| `OneTouchRepair.command` | Terminal fallback for the same one-click repair action |
| `Repair Sherlockdogs.command` | Terminal fallback for the same repair action |
| `Sherlockdogs Connect WeChat.app` | Optional Mac Personal Mode: bind your own WeChat self-chat |
| `Sherlockdogs Open Output.app` | View saved Markdown/results, preferred on Mac |
| `Uninstall Sherlockdogs.command` | Remove background services |
| `INSTALL_GUIDE_FOR_USERS.png` | User-facing picture guide |
| `INSTALL_GUIDE_FOR_USERS.svg` | Editable picture source |
| `IOS_SHORTCUTS_GUIDE.md` | Optional fallback guide, not the main Mac path |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Optional iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `MAC_PACKAGE_BRIEF.md` | Mac package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, include the latest Doctor output.

## If macOS blocks the app

This alpha uses local ad-hoc signing, not App Store notarization. If macOS blocks the first open, right-click `Sherlockdogs Start.app`, choose Open, then confirm Open.
If that still fails, run this in Terminal from the package folder: `xattr -dr com.apple.quarantine . && chmod +x "Configure Nutstore Inbox.command" "OneTouchRepair.command" "Repair Sherlockdogs.command" "Uninstall Sherlockdogs.command"`.
