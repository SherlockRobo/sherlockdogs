# Sherlockdogs 1.0 Public Beta

Tag: `v1.0.0-alpha.3-public-beta`

## Summary

Sherlockdogs 1.0 macOS public beta is ready for small-scope testing. Windows is not ready for the same product promise yet.

The beta paths are:

```text
macOS:
Start Sherlockdogs -> Connect WeChat -> forward to yourself in WeChat -> open local Markdown output

Windows target:
Start Sherlockdogs -> Connect local Windows WeChat -> forward to yourself in WeChat -> open local Markdown output

Windows current:
Not ready. The existing Windows folder is only an Inbox/Shortcut experiment and should not be promoted as the beta product.
```

## Platform Folders

| Platform | Folder |
|---|---|
| macOS | [Sherlockdogs-macos-alpha-1.0.0-alpha.3](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3) |
| Windows | Not ready; WeChat DB adapter pending |

## Install Guides

![Mac install guide](https://raw.githubusercontent.com/SherlockRobo/sherlockdogs/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/INSTALL_GUIDE_FOR_USERS.png)

## Start

| Platform | First step |
|---|---|
| macOS | Open `START_HERE.md`, double-click `Sherlockdogs Start.app`, then optional best path `Sherlockdogs Connect WeChat.app` |
| Windows | Do not promote yet; build Windows WeChat DB adapter first |

## Verified

- macOS beta gate passed.
- Windows static package gate passed for the old Inbox/Shortcut experiment only.
- Windows WeChat DB parity is not implemented.
- Mobile entry smoke evidence passed.
- Final release check passed.
- No zip, dmg, tar, or installer archive is published.

## Known Beta Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and local-only.
- Windows is not public-beta ready until it can match the Mac path: WeChat self-chat -> local desktop WeChat DB -> Markdown/Codex.

## Repository Landing Page

https://github.com/SherlockRobo/sherlockdogs
