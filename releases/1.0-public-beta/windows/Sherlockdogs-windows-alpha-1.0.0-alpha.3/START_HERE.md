# Start Here: Sherlockdogs Windows Alpha 小范围测试

## 30-second path

1. Open `INSTALL_GUIDE_FOR_USERS.png`.
2. Keep Windows WeChat logged in.
3. Double-click `Sherlockdogs Start.cmd`.
4. Double-click `Sherlockdogs Connect WeChat.cmd`; it can bind an existing decrypted DB folder or try the local decrypt helper. Windows will ask for Administrator permission when key extraction is needed. First connection uses discovery receiver `*` so phone-to-self WeChat is not missed.
5. Forward one test item to yourself in phone WeChat; Windows WeChat must receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. Run `Run Windows WeChat Smoke.cmd` for the guided real `#2` test. It generates a one-time smoke token, asks you to send that exact text to yourself, only passes evidence that contains the token, and exports a Desktop evidence folder at the end.
8. If anything fails, double-click `OneClick Codex Help.cmd`. It exports evidence, writes a Codex repair prompt, and starts Codex automatically when the CLI is available.
9. Double-click `Export Windows Evidence.cmd` to copy the latest evidence and Doctor report into a Desktop folder you can send back as-is. Do not zip it unless the operator explicitly asks for an archive.

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
| `IOS_SHORTCUTS_GUIDE.md` | Optional fallback phone share action guide |
| `shortcuts/Send-to-Sherlockdogs-Inbox.shortcut` | Optional fallback iOS Shortcut seed |
| `INSTALL_GUIDE_FOR_AI.md` | AI/support install guide |
| `WINDOWS_PACKAGE_BRIEF.md` | Windows package size, entrypoints, and system changes |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | Product intro, open-source components, and risk disclosure |

## Report back

If there is a failure, run `OneClick Codex Help.cmd` first. If Codex is not available, run `Export Windows Evidence.cmd`, then follow `RETURN_WINDOWS_EVIDENCE.md`: send the Desktop evidence folder back as-is.
