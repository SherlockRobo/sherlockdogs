# Sherlockdogs 1.0 Public Beta

Tag: `v1.0.0-alpha.3-public-beta`

Sherlockdogs turns phone WeChat self-chat items into local Markdown files and optional Codex tasks.

## What Is New

- macOS beta folder is ready for public beta testing.
- macOS self-chat -> local WeChat DB -> Markdown/Codex path has passed real smoke.
- Windows alpha.3 folder now includes the Mac-like WeChat DB adapter path, local decrypt bootstrap, incremental decrypt in the watcher, hidden scheduled tasks, and four top-level one-click entries: install, configure, repair, and report.
- iOS Shortcut / Inbox capture remains available as a fallback path.
- User-facing docs now include `START_HERE.md`, install guide images, troubleshooting notes, and evidence return instructions.

## Downloads

| Platform | Folder |
|---|---|
| macOS | [`Sherlockdogs-macos-alpha-1.0.0-alpha.3`](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/macos/Sherlockdogs-macos-alpha-1.0.0-alpha.3) |
| Windows | [`Sherlockdogs-windows-alpha-1.0.0-alpha.3`](https://github.com/SherlockRobo/sherlockdogs/tree/main/releases/1.0-public-beta/windows/Sherlockdogs-windows-alpha-1.0.0-alpha.3) |

No zip, dmg, tar, or installer archive is published for this beta. Open the platform folder and read `START_HERE.md`.

## Main Path

```text
phone WeChat -> forward to yourself
desktop WeChat -> receives the message
Sherlockdogs -> reads local desktop WeChat DB after opt-in setup
Markdown -> raw + metadata + README
Codex -> optional task when # or #2 is present
```

## Verified

- macOS beta gate passed.
- macOS self-chat DB path passed.
- Mobile entry smoke evidence passed.
- Windows runtime/static package gate passed.
- Final release check passed.

## Pending

- Windows should still be treated as beta because WeChat DB decrypt/key behavior depends on machine, WeChat version, and local permissions.

## Known Notes

- First launch may spend a few minutes installing Python dependencies.
- macOS may require right-click -> Open.
- Mac WeChat Personal Mode is opt-in and local-only.
- If Windows fails, run `3 OneClick Repair.cmd`; if Codex is unavailable, run `4 OneClick Report.cmd` and send back the generated evidence folder.
- iOS Shortcut / Inbox is fallback, not the default public-beta path.
