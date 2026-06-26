# Obsidian Setup

Sherlockdogs writes plain Markdown files. Obsidian is only the reader.

## One-Click Path

1. Double-click `1 OneClick Install.cmd`.
2. Double-click `2 OneClick Configure.cmd`.
3. When it asks for a vault folder, choose the folder you open in Obsidian.
4. In Obsidian, open that same folder as a vault.

Sherlockdogs then uses:

| Purpose | Folder |
|---|---|
| Obsidian vault root | the folder you selected |
| Saved articles/results | `<vault>\clipping` |
| WeChat article results | `<vault>\clipping\wechat` |
| Sherlockdogs queue/log state | `<vault>\clipping\_sherlockdogs` |
| Manual Inbox fallback | `%USERPROFILE%\Sherlockdogs\Inbox` |
| Sherlockdogs config | `%USERPROFILE%\.sherlockdogs\config.ps1` |

Do not edit `_sherlockdogs` unless support asks you to. It is runtime state.

## If Output Goes To The Wrong Folder

Run `2 OneClick Configure.cmd` again and choose the correct Obsidian vault folder.

Then run:

```text
Open Sherlockdogs Output.cmd
```

That opens the current `clipping` folder configured in Sherlockdogs.
