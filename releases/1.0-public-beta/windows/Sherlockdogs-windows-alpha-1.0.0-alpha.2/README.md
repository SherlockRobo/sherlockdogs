# Sherlockdogs Windows Alpha 小范围测试包

目标：Windows 用户不用接触个人微信数据库，也不用把内容交给 Sherlockdogs 云端。测试版使用用户自己的本地或同步 Inbox：手机把内容通过快捷指令、坚果云、OneDrive、Google Drive、Syncthing、NAS 或本地文件夹送到 `Sherlockdogs/Inbox`，电脑端自动入库，并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：自己的 Inbox

1. 先双击 `Sherlockdogs Start.cmd`，本地测试会使用默认 Inbox。
2. 如果要手机同步，选择自己的同步盘：坚果云、OneDrive、Google Drive、Syncthing 或 NAS。
3. 坚果云用户可双击 `Configure Nutstore Inbox.cmd` 自动检测同步目录，并创建：

```text
<坚果云同步目录>\Sherlockdogs\Inbox
<坚果云同步目录>\Sherlockdogs\Outbox
```

4. 手机端推荐用 iOS 快捷指令写入：

```text
Sherlockdogs/Inbox/
```

5. Windows 端看到 Inbox 文件后，Sherlockdogs 自动处理这个文件夹里的内容。

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

- 默认公测入口是用户自己的本地或同步 Inbox，不读取个人微信数据库。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- 后台使用当前用户的 Windows Scheduled Tasks。
- 当前 Mac 环境无法实际执行 PowerShell/Windows Scheduled Tasks；Windows 包已做静态 release gate，仍需要第一台 Windows 真机 smoke test。

## Windows smoke 证据

Windows runtime smoke 是开发/CI 验包流程，不放在用户可见发布包入口里。
