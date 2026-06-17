# Sherlockdogs Windows Alpha 小范围测试包

目标：Windows 用户不用接触个人微信数据库，也不用把内容交给 Sherlockdogs 云端。测试版的 Windows 手机入口是 iOS Shortcut/手机分享动作；微信内容需要先在手机上分享或复制到快捷指令，再写入用户自己的同步 Inbox。OneDrive、iCloud Drive for Windows、Google Drive、Syncthing、NAS、坚果云、本地 Inbox 都只是后台传输层。电脑端收到后在本机入库，并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：iOS Shortcut / 手机分享动作

1. 先双击 `Sherlockdogs Start.cmd`，让电脑端保持运行。
2. 按 `IOS_SHORTCUTS_GUIDE.md` 创建或导入 `发送到 Sherlockdogs` 快捷指令。
3. 在手机微信、浏览器、X、小红书、文件 App 里分享链接/文字/图片/文件到这个快捷指令。
4. 快捷指令把内容写到用户自己的后台传输目录：OneDrive、iCloud Drive for Windows、Google Drive、Syncthing、NAS、坚果云，或本地测试 Inbox。
5. 坚果云用户可双击 `Configure Nutstore Inbox.cmd` 自动检测同步目录，并创建：

```text
<坚果云同步目录>\Sherlockdogs\Inbox
<坚果云同步目录>\Sherlockdogs\Outbox
```

6. Windows 端收到后台传输文件后，Sherlockdogs 自动入库并生成本地 Markdown。

注意：Windows Alpha 当前不读取 Windows 微信数据库，也不会自动抓“手机微信发给自己的聊天消息”。Mac 的 `Sherlockdogs Connect WeChat.app` 是另一条本机 DB 路径，Windows 版暂未提供同款 adapter。

## 双击入口

- `Sherlockdogs Start.cmd`：安装 + 生成诊断报告
- `Configure Nutstore Inbox.cmd`：可选，把 Inbox 切换到用户自己的坚果云同步目录
- `Open Sherlockdogs Output.cmd`：打开入库后的 clipping 输出目录
- `Doctor Sherlockdogs.cmd`：检查状态并生成诊断报告
- `Uninstall Sherlockdogs.cmd`：卸载后台任务
- `INSTALL_GUIDE_FOR_USERS.png`：给用户看的图形安装说明
- `INSTALL_GUIDE_FOR_USERS.svg`：可编辑图源
- `INSTALL_GUIDE_FOR_AI.md`：给 AI/客服看的安装说明

## 默认入口

- Inbox：`%USERPROFILE%\Sherlockdogs\Inbox`
- 输出：优先 `%USERPROFILE%\ObsidianVault_LOCAL\clipping`，否则 `%USERPROFILE%\Sherlockdogs\Vault\clipping`
- 配置：`%USERPROFILE%\.sherlockdogs\config.ps1`
- Python venv：`%USERPROFILE%\.sherlockdogs\venv`

## 公测边界

- 默认公测入口是 iOS Shortcut/手机分享动作；Inbox/同步盘只是后台传输层，不读取个人微信数据库。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- 后台使用当前用户的 Windows Scheduled Tasks。
- 当前 Mac 环境无法实际执行 PowerShell/Windows Scheduled Tasks；Windows 包已做静态 release gate，仍需要第一台 Windows 真机 smoke test。

## Windows smoke 证据

Windows runtime smoke 是开发/CI 验包流程，不放在用户可见发布包入口里。
