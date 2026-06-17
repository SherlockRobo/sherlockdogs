# Start Here: Sherlockdogs Windows Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Prepare a decrypted local Windows WeChat DB folder that contains `message\message_*.db`.
3. Double-click `Sherlockdogs Start.cmd`.
4. Double-click `Sherlockdogs Connect WeChat.cmd`.
5. Forward one test item to yourself in phone WeChat; Windows WeChat must receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. If anything fails, run `Doctor Sherlockdogs.cmd`.

## What this beta does

- Uses Windows WeChat local DB adapter for the Mac-like self-chat path.
- Saves and processes clippings locally after Windows WeChat receives the self-chat item and the local DB adapter reads it.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Reads decrypted local Windows WeChat DB files after explicit Connect.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `Sherlockdogs Start.cmd` | First install |
| `Sherlockdogs Connect WeChat.cmd` | Bind decrypted Windows WeChat DB folder and start self-chat watcher |
| `Configure Nutstore Inbox.cmd` | Optional experimental fallback: switch Inbox to your own synced folder |
| `Open Sherlockdogs Output.cmd` | View saved Markdown/results |
| `Doctor Sherlockdogs.cmd` | Generate diagnostics |
| `Uninstall Sherlockdogs.cmd` | Remove background tasks |
| `INSTALL_GUIDE_FOR_USERS.png` | User-facing picture guide |
| `INSTALL_GUIDE_FOR_USERS.svg` | Editable picture source |
| `IOS_SHORTCUTS_GUIDE.md` | Optional fallback guide, not the main Windows product path |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Optional iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `WINDOWS_PACKAGE_BRIEF.md` | Windows package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, include the latest Doctor output.
