# Sherlockdogs 1.0.0-alpha.3 Windows Alpha Hotfix 小范围测试包

Alpha.3 folds the first real Windows onboarding lessons back into the package:

- Windows WeChat polling now runs incremental decrypt before reading the decrypted DB.
- Queue and run state move to the configured work folder, normally `<clipping>\_sherlockdogs`.
- Receiver files are written/read as UTF-8 without BOM.
- Scheduled tasks use a hidden VBS launcher when available, avoiding repeated PowerShell flashes.
- The package now has four top-level user entries: `1 OneClick Install.cmd`, `2 OneClick Configure.cmd`, `3 OneClick Repair.cmd`, and `4 OneClick Report.cmd`.
- `2 OneClick Configure.cmd` guides Obsidian vault/output path setup, writes `config.ps1`, then connects Windows WeChat.
- `3 OneClick Repair.cmd` exports evidence, writes a repair prompt, and starts Codex when the CLI is available.
- The Windows WeChat DB adapter no longer turns generic `web` URLs from WeChat XML, such as cover images, into standalone jobs.

Start here:

1. Open `INSTALL_GUIDE_FOR_USERS.png` for the picture guide.
2. Double-click `1 OneClick Install.cmd`.
3. Double-click `2 OneClick Configure.cmd`. It chooses the Obsidian vault/output path and then connects Windows WeChat. If no decrypted DB folder exists, it tries to install and run the local wechat-decrypt helper. Windows will ask for Administrator permission when key extraction is needed. First connection uses discovery receiver `*` so phone-to-self WeChat is not missed; the smoke flow saves the discovered `receiver_chat`.
4. Confirm it found a local Windows WeChat DB folder containing `message\message_*.db` or equivalent message DB files.
5. Forward a test item to yourself in phone WeChat and let Windows WeChat receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. Run `Run Windows WeChat Smoke.cmd` for the guided real `#2` test. It generates a one-time smoke token, asks you to send that exact text to yourself, only passes evidence that contains the token, and exports a Desktop evidence folder at the end.
8. If anything fails, run `3 OneClick Repair.cmd` first. It will export evidence and try to open a Codex repair task.
9. Double-click `4 OneClick Report.cmd` to copy the latest evidence and Doctor report into a Desktop folder that can be sent back as-is. Do not zip it unless the operator explicitly asks for an archive.
10. Run `Doctor Sherlockdogs.cmd` if anything looks wrong.
11. Read `WINDOWS_PACKAGE_BRIEF.md` and `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` before sharing with another tester.

Boundary: this Windows alpha includes a Windows WeChat DB adapter and a local decrypt bootstrap. The decrypt helper runs locally and may require Windows WeChat to be logged in and Administrator PowerShell for key extraction. It does not use a Sherlockdogs relay. Obsidian is recommended as the Markdown library reader, but is not required for Codex cards.
