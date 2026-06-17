# Share Sherlockdogs 1.0 Small Beta

Generated: 2026-06-17T09:38:12+0800

## Send these folders

| Tester platform | Folder |
|---|---|
| Mac | `<local-sherlockdogs-workdir>/dist/macos-beta/Sherlockdogs-macos-alpha-1.0.0-alpha.3` |
| Windows | `<local-sherlockdogs-workdir>/dist/windows-beta/Sherlockdogs-windows-alpha-1.0.0-alpha.2` |

Send the whole folder as-is. Do not send only the top-level command files.

## Message to tester

Please open `START_HERE.md` first.

This is a small-scope test build. The product promise is: send anything to your own Inbox, keep a local Markdown library, and optionally continue in Codex.

For the shortest test:

- Mac: open `INSTALL_GUIDE_FOR_USERS.png`, double-click `Sherlockdogs Start.app`, then double-click `Sherlockdogs Connect WeChat.app` and forward one test item to yourself in WeChat.
- Windows: open `INSTALL_GUIDE_FOR_USERS.png`, double-click `Sherlockdogs Start.cmd`, then `Sherlockdogs Connect WeChat.cmd` after preparing decrypted Windows WeChat DBs. Full Windows parity still needs a real Windows self-chat smoke before public promotion.
- If macOS blocks the app after copying/downloading, right-click `Sherlockdogs Start.app`, choose Open, then confirm Open.

If anything fails, run `Doctor Sherlockdogs`, open `Open Sherlockdogs Diagnostics`, and send the newest doctor report.

## Privacy

This beta uses your own local storage by default. On Mac, WeChat Personal Mode is opt-in and reads the local Mac WeChat database only after you run `Sherlockdogs Connect WeChat.app`. On Windows, `Sherlockdogs Connect WeChat.cmd` reads a decrypted local Windows WeChat DB directory after explicit setup. Sherlockdogs does not upload clipping content to a Sherlockdogs relay service by default.

Obsidian is recommended for browsing the Markdown library, but is not required for Codex cards.
