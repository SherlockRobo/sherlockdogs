# Sherlockdogs Windows Package Brief

## 核心结论

Windows 测试包是给普通用户双击运行的本地版 Sherlockdogs。它不读取 Windows 微信数据库，不使用 Sherlockdogs 云中转；Windows 手机入口是 iOS Shortcut/手机分享动作，OneDrive、iCloud Drive for Windows、Google Drive、Syncthing、NAS、坚果云、本地 Inbox 只是后台传输层。电脑端收到文件后在本机入库，并按指令进入 Codex 对话。

## 包信息

| 项目 | 内容 |
|---|---|
| 平台 | Windows |
| 版本 | `1.0.0-alpha.2` |
| 包目录 | `Sherlockdogs-windows-alpha-1.0.0-alpha.2` |
| 当前大小 | `564K`，以当前 release 目录 `du -sh` 实测 |
| 默认入口 | `Sherlockdogs Start.cmd` |
| 手机入口 | `IOS_SHORTCUTS_GUIDE.md` + 用户自己的同步 Inbox |
| 可选配置入口 | `Configure Nutstore Inbox.cmd` |
| 诊断入口 | `Doctor Sherlockdogs.cmd` |
| 输出入口 | `Open Sherlockdogs Output.cmd` |

## 用户使用

1. 准备一个手机和 Windows 都能看到的同步目录：OneDrive、iCloud Drive for Windows、Google Drive、Syncthing、NAS、坚果云，或本地测试 Inbox。
2. 打开 `INSTALL_GUIDE_FOR_USERS.png`。
3. 双击 `Sherlockdogs Start.cmd`。
4. 按 `IOS_SHORTCUTS_GUIDE.md` 创建或导入 `发送到 Sherlockdogs` 快捷指令。
5. 手机分享链接、微信文章、图片、PDF、视频、文本到快捷指令；快捷指令和同步盘只负责后台传输。
6. Windows 同步后自动入库；用 `Open Sherlockdogs Output.cmd` 查看结果。

## 系统改动

| 改动 | 说明 |
|---|---|
| 用户配置 | 写入 `%USERPROFILE%\.sherlockdogs\config.ps1` |
| Python 环境 | 创建或复用 `%USERPROFILE%\.sherlockdogs\venv` |
| 后台服务 | 创建当前用户的 Windows Scheduled Tasks |
| 本地输出 | 写入用户配置的 clipping 目录 |
| 卸载 | `Uninstall Sherlockdogs.cmd` 只卸载后台任务，不删除用户内容 |

## 包内主要文件

| 文件 | 用途 |
|---|---|
| `INSTALL_GUIDE_FOR_USERS.png` | 给用户看的图形安装说明 |
| `INSTALL_GUIDE_FOR_AI.md` | 给 AI/客服看的安装说明 |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | 产品介绍、依赖、风险披露 |
| `START_HERE.md` | 用户第一步说明 |
| `README.md` | 完整 Windows 测试包说明 |
| `TROUBLESHOOTING.md` | 常见问题 |
| `CHECKSUMS.txt` | 包内文件校验 |

## 当前边界

Windows 包已通过本机静态 release gate。正式发给更多用户前，仍建议在真实 Windows 机器上做一次安装、iOS Shortcut 写入同步 Inbox、文件入库、Codex 卡片触发的 smoke test。当前 Windows Alpha 不承诺读取 Windows 微信 DB；要做到 Mac 同款微信自聊抓取，需要单独补 Windows WeChat DB adapter。
