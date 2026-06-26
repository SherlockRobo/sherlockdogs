# Start Here: Sherlockdogs Windows Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Keep Windows WeChat logged in.
3. Double-click `1 OneClick Install.cmd`.
4. Double-click `2 OneClick Configure.cmd`; it chooses the Obsidian vault/output path, then binds or prepares Windows WeChat DB. Windows will ask for Administrator permission when key extraction is needed.
5. Forward one test item to yourself in phone WeChat; Windows WeChat must receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. Run `Run Windows WeChat Smoke.cmd` for the guided real `#2` test. It generates a one-time smoke token, asks you to send that exact text to yourself, only passes evidence that contains the token, and exports a Desktop evidence folder at the end.
8. If anything fails, double-click `3 OneClick Repair.cmd`. It exports evidence, writes a Codex repair prompt, and starts Codex automatically when the CLI is available.
9. To send logs back, double-click `4 OneClick Report.cmd`. Do not zip the evidence folder unless the operator explicitly asks for an archive.

## What this beta does

- Uses Windows WeChat local DB adapter for the Mac-like self-chat path.
- Tries to bootstrap a local decrypt helper when no decrypted DB folder is already configured.
- Runs incremental decrypt before each Windows WeChat poll so newly received messages are not missed.
- Keeps Sherlockdogs queue/runs under the clipping `_sherlockdogs` work folder instead of inside the downloaded package.
- Saves and processes clippings locally after Windows WeChat receives the self-chat item and the local adapter reads it.
- Recommends Obsidian as the local Markdown library reader, but does not require it.
- Can trigger Codex tasks through `#1/#2/#3/#4/#5`.
- Reads decrypted local Windows WeChat DB files after explicit Connect.
- Does not upload clipping content to a Sherlockdogs relay service by default.

## Command guide

| Command | Use it when |
|---|---|
| `1 OneClick Install.cmd` | First install: Python venv, dependencies, background tasks, Doctor report |
| `2 OneClick Configure.cmd` | Choose Obsidian vault/output path, set `clipping` / `_sherlockdogs`, and connect Windows WeChat |
| `3 OneClick Repair.cmd` | One-click repair path: export evidence, create a Codex prompt, and start a Codex repair task if available |
| `4 OneClick Report.cmd` | One-click report path: export the Desktop evidence folder for return |
| `Sherlockdogs Start.cmd` | First install |
| `Sherlockdogs Connect WeChat.cmd` | Bind or prepare Windows WeChat DB and start self-chat watcher |
| `Run Windows WeChat Smoke.cmd` | Guided full path test: connect, ask for a tokenized real `#2` self-chat, collect matching evidence, then export a Desktop evidence folder |
| `Collect Windows WeChat Evidence.cmd` | Generate the Windows DB smoke report after a real `#2` test |
| `Export Windows Evidence.cmd` | Copy the latest smoke report and Doctor report into a Desktop folder for return |
| `OneClick Codex Help.cmd` | One-click repair path: export evidence, create a Codex prompt, and start a Codex repair task if available |
| `RETURN_WINDOWS_EVIDENCE.md` | What to send back after a pass or failure |
| `Configure Nutstore Inbox.cmd` | Optional fallback: switch Inbox to your own synced folder |
| `Open Sherlockdogs Output.cmd` | View saved Markdown/results |
| `Doctor Sherlockdogs.cmd` | Generate diagnostics |
| `Uninstall Sherlockdogs.cmd` | Remove background tasks |
| `INSTALL_GUIDE_FOR_USERS.png` | User-facing picture guide |
| `INSTALL_GUIDE_FOR_USERS.svg` | Editable picture source |
| `OBSIDIAN_SETUP.md` | How to choose the Obsidian vault and where results go |
| `IOS_SHORTCUTS_GUIDE.md` | Optional fallback phone share action guide |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Optional fallback iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `WINDOWS_PACKAGE_BRIEF.md` | Windows package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, run `3 OneClick Repair.cmd` first. If Codex is not available, run `4 OneClick Report.cmd`, then follow `RETURN_WINDOWS_EVIDENCE.md`: send the Desktop evidence folder back as-is.
