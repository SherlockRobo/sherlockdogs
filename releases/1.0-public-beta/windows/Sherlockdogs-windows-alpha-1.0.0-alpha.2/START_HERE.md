# Start Here: Sherlockdogs Windows Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Keep Windows WeChat logged in.
3. Double-click `Sherlockdogs Start.cmd`.
4. Double-click `Sherlockdogs Connect WeChat.cmd`; it can bind an existing decrypted DB folder or try the local decrypt helper.
5. Forward one test item to yourself in phone WeChat; Windows WeChat must receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. Run `Run Windows WeChat Smoke.cmd` for the guided real `#2` test, or `Collect Windows WeChat Evidence.cmd` if you already sent the test item.
8. If anything fails, run `Doctor Sherlockdogs.cmd`.

## What this beta does

- Uses Windows WeChat local DB adapter for the Mac-like self-chat path.
- Tries to bootstrap a local decrypt helper when no decrypted DB folder is already configured.
- Saves and processes clippings locally after Windows WeChat receives the self-chat item and the local adapter reads it.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Reads decrypted local Windows WeChat DB files after explicit Connect.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `Sherlockdogs Start.cmd` | First install |
| `Sherlockdogs Connect WeChat.cmd` | Bind or prepare Windows WeChat DB and start self-chat watcher |
| `Run Windows WeChat Smoke.cmd` | Guided full path test: connect, ask for a real `#2` self-chat, then collect evidence |
| `Collect Windows WeChat Evidence.cmd` | Generate the Windows DB smoke report after a real `#2` test |
| `Configure Nutstore Inbox.cmd` | Optional fallback: switch Inbox to your own synced folder |
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
