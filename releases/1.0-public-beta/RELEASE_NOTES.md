# Sherlockdogs 1.0 Public Beta

Tag: `v1.0.0-alpha.3-public-beta`

## Summary

Sherlockdogs 1.0 public beta is ready for small-scope testing.

The beta paths are:

```text
macOS:
Start Sherlockdogs -> Connect WeChat -> forward to yourself in WeChat -> open local Markdown output

Windows:
Start Sherlockdogs -> iOS Shortcut / phone share -> synced Inbox -> open local Markdown output
```

## Platform Folders

| Platform | Folder |
|---|---|
| macOS | [Sherlockdogs-macos-alpha-1.0.0-alpha.3](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3) |
| Windows | [Sherlockdogs-windows-alpha-1.0.0-alpha.2](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2) |

## Install Guides

| macOS | Windows |
|---|---|
| ![Mac install guide](https://raw.githubusercontent.com/SherlockRobo/sherlockdogs/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3/INSTALL_GUIDE_FOR_USERS.png) | ![Windows install guide](https://raw.githubusercontent.com/SherlockRobo/sherlockdogs/main/releases/1.0-public-beta/windows/Sherlockdogs-windows-alpha-1.0.0-alpha.2/INSTALL_GUIDE_FOR_USERS.png) |

## Start

| Platform | First step |
|---|---|
| macOS | Open `START_HERE.md`, double-click `Sherlockdogs Start.app`, then optional best path `Sherlockdogs Connect WeChat.app` |
| Windows | Open `START_HERE.md`, double-click `Sherlockdogs Start.cmd`, then create the phone share action from `IOS_SHORTCUTS_GUIDE.md` |

## Verified

- macOS beta gate passed.
- Windows static package gate passed.
- Windows runtime smoke evidence passed.
- Mobile entry smoke evidence passed.
- Final release check passed.
- No zip, dmg, tar, or installer archive is published.

## Known Beta Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and local-only.
- Windows Alpha uses iOS Shortcut / phone share action plus a synced Inbox. It does not read Windows WeChat DB.

## Repository Landing Page

https://github.com/SherlockRobo/sherlockdogs
