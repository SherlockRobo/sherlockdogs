# Share Sherlockdogs 1.0 Small Beta

Generated: 2026-06-16T19:49:57+0800

## Send this folder

| Tester platform | Folder |
|---|---|
| Mac | `<local-sherlockdogs-workdir>/dist/macos-beta/Sherlockdogs-macos-alpha-1.0.0-alpha.3` |

Send the whole Mac folder as-is. Do not send only the top-level app files.

Do not promote the Windows folder yet. It is only an Inbox/Shortcut experiment and does not match the Mac WeChat self-chat product path.

## Message to tester

Please open `START_HERE.md` first.

This is a small-scope macOS test build. The product promise is: forward to your own WeChat, let the local Mac adapter read the desktop WeChat DB, keep a local Markdown library, and optionally continue in Codex.

For the shortest test:

- Mac: open `INSTALL_GUIDE_FOR_USERS.png`, double-click `Sherlockdogs Start.app`, then double-click `Sherlockdogs Connect WeChat.app` and forward one test item to yourself in WeChat.
- If macOS blocks the app after copying/downloading, right-click `Sherlockdogs Start.app`, choose Open, then confirm Open.
- Windows is pending until it supports the same path: phone WeChat -> self-chat -> local Windows WeChat DB -> Markdown/Codex.

If anything fails, run `Doctor Sherlockdogs`, open `Open Sherlockdogs Diagnostics`, and send the newest doctor report.

## Privacy

This beta uses local desktop processing. On Mac, WeChat Personal Mode is opt-in and reads the local Mac WeChat database only after you run `Sherlockdogs Connect WeChat.app`. Sherlockdogs does not upload clipping content to a Sherlockdogs relay service by default.

Obsidian is recommended for browsing the Markdown library, but is not required for Codex cards.
