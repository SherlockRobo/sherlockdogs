# Phone to Cloud Inbox

Windows Alpha uses a user-owned sync folder as the bridge for phone capture.
Sherlockdogs does not receive, proxy, or store the user's clipping content.

OneDrive or iCloud Drive for Windows is the simplest Windows phone path when
available. Nutstore is optional, not a hard dependency. Google Drive, Syncthing,
NAS, or a plain local folder can also be used as long as the desktop sees the
same `Sherlockdogs/Inbox` folder.

## Target Folder

Create or use this folder in your chosen sync drive:

```text
Sherlockdogs/Inbox
```

Desktop Sherlockdogs watches the synced local copy after running Start. If you
use Nutstore, run the helper below. If you use iCloud/Google Drive/OneDrive,
select or pass that folder path as the Sherlockdogs Inbox.

- macOS local-only: `Sherlockdogs Start.app` is enough.
- macOS Nutstore: `Configure Nutstore Inbox.command`
- Windows local-only: `Sherlockdogs Start.cmd` is enough.
- Windows Nutstore: `Configure Nutstore Inbox.cmd`

## Simple Phone Path

1. Pick a sync provider: Nutstore, iCloud Drive, Google Drive, OneDrive, Syncthing, or local folder.
2. Create `Sherlockdogs/Inbox`.
3. From WeChat, X, Xiaohongshu, a browser, or a file app, use the iOS Shortcut or share/save the link/file into `Sherlockdogs/Inbox`.
4. Wait for the sync provider to sync to the desktop.
5. Sherlockdogs imports the item locally.
6. Obsidian is recommended for browsing the Markdown library, but is not required for Codex cards.

## Text File Format

For links or text, save a `.txt` or `.md` file like this:

```text
https://example.com/article-or-video
#2
```

Command levels:

| Command | Meaning |
|---|---|
| empty or `#1` | Save only |
| `#2` or `#` | Save and create a Codex card |
| `#3` | Extract summary/metadata |
| `#4` or `#ob` | Deep read |
| `#5` | Key frames/screenshots/segments |

## iOS Shortcut Draft

Use this as the first manual Shortcut recipe:

1. Input: Share Sheet input.
2. Ask for text: command, default `#2`.
3. Get current date, format `yyyyMMdd-HHmmss`.
4. Make text:

```text
{Share Sheet input}
{command}
```

5. Save file name: `sdogs-{date}.txt`.
6. Save or upload to the chosen cloud Inbox.

For Nutstore WebDAV:

```text
PUT https://dav.jianguoyun.com/dav/Sherlockdogs/Inbox/sdogs-{date}.txt
```

Use the user's Nutstore email and Nutstore app password for WebDAV auth.
Do not use the normal account password if Nutstore provides an app password.

For iCloud Drive:

```text
Save File -> iCloud Drive/Sherlockdogs/Inbox/sdogs-{date}.txt
```

For OneDrive:

```text
Save File -> OneDrive/Sherlockdogs/Inbox/sdogs-{date}.txt
```

## Privacy Boundary

- The sync provider is the user's own account.
- Sherlockdogs only watches the local synced folder on the desktop.
- Obsidian is recommended, not required; the durable output is local Markdown.
- Windows Alpha does not read Windows personal WeChat databases.
- Mac Personal Mode is separate: it can read the local Mac WeChat database only after the user runs `Sherlockdogs Connect WeChat.app`.
- The public beta does not upload clipping content to a Sherlockdogs relay service by default.
