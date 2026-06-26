# Sherlockdogs Public Beta Troubleshooting

## First checks

Run these first:

- macOS: `Preflight Sherlockdogs.command`, then `Doctor Sherlockdogs.command`
- Windows: `Preflight Sherlockdogs.cmd`, then `Doctor Sherlockdogs.cmd`

If the first run fails, open:

- `Open Sherlockdogs Diagnostics`
- `Open Sherlockdogs Output`

## Common failures

| Symptom | Meaning | Fix |
|---|---|---|
| Python missing | Sherlockdogs cannot run scripts | Install Python 3, then run First Run again |
| Sync folder not found | Sherlockdogs cannot auto-detect the optional synced Inbox fallback | Use WeChat Connect as the main path, or configure your own fallback folder |
| Windows WeChat DB not connected | Windows self-chat watcher has no local DB path | Run `Sherlockdogs Connect WeChat.cmd` with Windows WeChat logged in |
| pypi.org unreachable | Dependencies cannot be installed | Change network/VPN/proxy, then run Install again |
| Codex missing | Clippings can save, but AI chatbox tasks will not start | Install/open Codex, or set `CODEX_BIN` |
| ffprobe missing | Video duration/metadata may be incomplete | Install ffmpeg/ffprobe |
| Background service/task missing | Watcher or runner did not register | Run Install again |
| Failed jobs exist | Some item could not be processed | Send the latest doctor report from Diagnostics |
| macOS blocks app | App is not notarized or copied with quarantine | Right-click the `.app`, choose Open, confirm Open; if it still fails, run `Fix Sherlockdogs Mac Open Permissions.command` |

## Public beta boundary

The recommended public beta path is WeChat self-chat: phone WeChat -> desktop WeChat -> local Sherlockdogs adapter -> Markdown/Codex. Mac reads local Mac WeChat data only after `Sherlockdogs Connect WeChat.app`. Windows prepares or binds a local Windows WeChat DB path only after `Sherlockdogs Connect WeChat.cmd`. Inbox/Shortcut/sync folders are fallback paths. Sherlockdogs does not upload clipping content to a Sherlockdogs relay service by default.

Obsidian is recommended for browsing the local Markdown library, but it is not required for saving files or creating Codex cards.
