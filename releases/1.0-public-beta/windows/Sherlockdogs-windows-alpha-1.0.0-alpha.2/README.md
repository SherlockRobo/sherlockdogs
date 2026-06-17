# Sherlockdogs Windows Alpha 小范围测试包

目标：Windows 用户使用和 Mac 一样的产品路径：手机微信发给自己，Windows 微信收到，本机 Sherlockdogs 读取本地 Windows 微信 DB，自动入库并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。

当前 Alpha 已包含 Windows WeChat DB adapter 和 `Sherlockdogs Connect WeChat.cmd`。边界是：Connect 需要用户提供已经解密好的本地 Windows WeChat DB 目录，里面应包含 `message\message_*.db` 或等价 message DB 文件。取 key / 解密层需要在 Windows 真机上接入和验证。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：微信发给自己

1. 先双击 `Sherlockdogs Start.cmd`，让电脑端保持运行。
2. 准备一个已解密的 Windows 微信 DB 目录，至少包含 `message\message_*.db`。
3. 双击 `Sherlockdogs Connect WeChat.cmd`，选择这个 DB 目录。
4. 手机微信转发一条内容给自己的微信号。
5. Windows 微信收到后，Sherlockdogs 读取本地 DB，自动入库并生成本地 Markdown / Codex 任务。

## 双击入口

- `Sherlockdogs Start.cmd`：安装 + 生成诊断报告
- `Sherlockdogs Connect WeChat.cmd`：绑定已解密的 Windows 微信 DB 目录 + 启动微信自聊监听
- `Configure Nutstore Inbox.cmd`：可选实验兜底，把 Inbox 切换到用户自己的同步目录；不是主路径
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
- Windows WeChat DB：`%USERPROFILE%\.sherlockdogs\config.ps1` 里的 `SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR`

## 公测边界

- 默认目标入口是手机微信发给自己；Windows 本机读取已解密的本地微信 DB。
- 当前还需要 Windows 真机补齐并验证取 key / 解密层；未验证前不要把 Windows 标成 Mac 同款已完成。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- 后台使用当前用户的 Windows Scheduled Tasks。
- 当前 Mac 环境无法实际执行 PowerShell/Windows Scheduled Tasks；Windows 包已做静态 adapter smoke，仍需要第一台 Windows 真机 DB smoke test。

## Windows smoke 证据

Windows runtime smoke 是开发/CI 验包流程，不放在用户可见发布包入口里。
