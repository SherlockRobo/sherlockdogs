# Sherlockdogs 1.0 Public Beta

Tag: `v1.0.0-alpha.3-public-beta`

## Summary

Sherlockdogs 1.0 macOS public beta is ready for small-scope testing. Windows now has the Mac-like WeChat DB adapter in the alpha folder, but it still needs real Windows decrypt/self-chat smoke before it should be promoted as equal to macOS.

The beta paths are:

```text
macOS:
Start Sherlockdogs -> Connect WeChat -> forward to yourself in WeChat -> open local Markdown output

Windows target:
Start Sherlockdogs -> Connect local Windows WeChat -> forward to yourself in WeChat -> open local Markdown output

Windows current:
Packaged with Sherlockdogs Connect WeChat.cmd and a Windows WeChat DB adapter.
Requires decrypted Windows WeChat DBs and a real Windows smoke before full parity.
```

## Platform Folders

| Platform | Folder |
|---|---|
| macOS | [Sherlockdogs-macos-alpha-1.0.0-alpha.3](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3) |
| Windows | [Sherlockdogs-windows-alpha-1.0.0-alpha.2](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2) |

## Install Guides

![Mac install guide](https://raw.githubusercontent.com/SherlockRobo/sherlockdogs/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/INSTALL_GUIDE_FOR_USERS.png)

## Start

| Platform | First step |
|---|---|
| macOS | Open `START_HERE.md`, double-click `Sherlockdogs Start.app`, then optional best path `Sherlockdogs Connect WeChat.app` |
| Windows | Open `START_HERE.md`, double-click `Sherlockdogs Start.cmd`, then `Sherlockdogs Connect WeChat.cmd` with a decrypted Windows WeChat DB folder |

## Verified

- macOS beta gate passed.
- Windows static package gate passed.
- Windows WeChat DB adapter is packaged; real Windows decrypt/self-chat/Codex-card smoke is still pending.
- Mobile entry smoke evidence passed.
- Final release check passed.
- No zip, dmg, tar, or installer archive is published.

## Known Beta Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and local-only.
- Windows is not full public-beta ready until it passes the same path: WeChat self-chat -> local desktop WeChat DB -> Markdown/Codex.

## Repository Landing Page

https://github.com/SherlockRobo/sherlockdogs
