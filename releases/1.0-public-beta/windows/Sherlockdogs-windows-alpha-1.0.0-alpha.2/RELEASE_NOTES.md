# Sherlockdogs 1.0.0-alpha.2 Windows Alpha 小范围测试包

Start here:

1. Open `INSTALL_GUIDE_FOR_USERS.png` for the picture guide.
2. Double-click `Sherlockdogs Start.cmd`.
3. Double-click `Sherlockdogs Connect WeChat.cmd`. If no decrypted DB folder exists, it tries to install and run the local wechat-decrypt helper.
4. Confirm it found a local Windows WeChat DB folder containing `message\message_*.db` or equivalent message DB files.
5. Forward a test item to yourself in phone WeChat and let Windows WeChat receive it.
6. Open results with `Open Sherlockdogs Output.cmd`.
7. Run `Run Windows WeChat Smoke.cmd` for the guided real `#2` test. It generates a one-time smoke token, asks you to send that exact text to yourself, and only passes evidence that contains the token.
8. Run `Doctor Sherlockdogs.cmd` if anything looks wrong.
9. Read `WINDOWS_PACKAGE_BRIEF.md` and `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` before sharing with another tester.

Boundary: this Windows alpha includes a Windows WeChat DB adapter and a local decrypt bootstrap. The decrypt helper runs locally and may require Windows WeChat to be logged in and Administrator PowerShell for key extraction. It does not use a Sherlockdogs relay. Obsidian is recommended as the Markdown library reader, but is not required for Codex cards.
