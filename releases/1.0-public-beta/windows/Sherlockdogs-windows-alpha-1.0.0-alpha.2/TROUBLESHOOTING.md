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
| Sync folder not found | Sherlockdogs cannot auto-detect the optional synced Inbox | Use the default local Inbox, install/sign in your sync provider, or run the configure helper with the folder path |
| pypi.org unreachable | Dependencies cannot be installed | Change network/VPN/proxy, then run Install again |
| Codex missing | Clippings can save, but AI chatbox tasks will not start | Install/open Codex, or set `CODEX_BIN` |
| ffprobe missing | Video duration/metadata may be incomplete | Install ffmpeg/ffprobe |
| Background service/task missing | Watcher or runner did not register | Run Install again |
| Failed jobs exist | Some item could not be processed | Send the latest doctor report from Diagnostics |
| macOS blocks app | App is not notarized or copied with quarantine | Right-click the `.app`, choose Open, confirm Open; if it still fails, run `Fix Sherlockdogs Mac Open Permissions.command` |

## Public beta boundary

The default public beta uses the tester's own local or synced Inbox. Sherlockdogs only watches that local folder. The sync provider can be iCloud Drive, Nutstore, OneDrive, Google Drive, Syncthing, NAS, or a plain local folder. It does not read personal WeChat databases and does not upload clipping content to a Sherlockdogs relay service by default.

Obsidian is recommended for browsing the local Markdown library, but it is not required for saving files or creating Codex cards.
