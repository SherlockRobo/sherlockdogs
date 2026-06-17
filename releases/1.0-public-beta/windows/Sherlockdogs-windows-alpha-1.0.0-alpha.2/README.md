# Sherlockdogs Windows Alpha 小范围测试包

目标：Windows 用户使用和 Mac 一样的产品路径：手机微信发给自己，Windows 微信收到，本机 Sherlockdogs 读取本地 Windows 微信 DB，自动入库并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。

当前 Alpha 已包含 Windows WeChat DB adapter、`Sherlockdogs Connect WeChat.cmd` 和本地 decrypt bootstrap。Connect 会优先绑定已有解密 DB；如果找不到，会尝试安装并运行本地 `wechat-decrypt` helper，产出包含 `message\message_*.db` 或等价 message DB 文件的目录。真机上仍必须跑完整 smoke 后才能标成 Mac 同款完成。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：微信发给自己

1. 先双击 `Sherlockdogs Start.cmd`，让电脑端保持运行。
2. 保持 Windows 微信登录。
3. 双击 `Sherlockdogs Connect WeChat.cmd`；它会绑定已有解密 DB，或尝试本地解密 bootstrap。初次连接默认使用 discovery receiver `*`，先避免漏掉“手机微信发给自己”的真实聊天；跑通 smoke 后会自动保存发现的 `receiver_chat`。
4. 如果没有现成解密 DB，需要从正在运行的 Windows 微信取 key，请右键 `Sherlockdogs Connect WeChat.cmd`，选择“以管理员身份运行”。
5. 手机微信转发一条内容给自己的微信号。
6. Windows 微信收到后，Sherlockdogs 读取本地 DB，自动入库并生成本地 Markdown / Codex 任务。

## 双击入口

- `Sherlockdogs Start.cmd`：安装 + 生成诊断报告
- `Sherlockdogs Connect WeChat.cmd`：准备/绑定 Windows 微信 DB + 启动微信自聊监听
- `Run Windows WeChat Smoke.cmd`：引导完整真机测试：生成一次性 token，提示手机把含 `#2` 和 token 的文本发给自己，只采集匹配 token 的证据
- `Collect Windows WeChat Evidence.cmd`：真实 `#2` 自聊测试后生成 Windows DB smoke 证据；向导模式会自动加 token 校验
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
- Windows WeChat DB：`%USERPROFILE%\.sherlockdogs\config.ps1` 里的 `SHERLOCKDOGS_WINDOWS_WECHAT_DECRYPTED_DIR`

## 公测边界

- 默认目标入口是手机微信发给自己；Windows 本机读取已解密的本地微信 DB。
- 当前还需要 Windows 真机验证取 key / 解密 -> 自聊入库 -> Codex 卡片；未验证前不要把 Windows 标成 Mac 同款已完成。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- 后台使用当前用户的 Windows Scheduled Tasks。
- 当前 Mac 环境无法实际执行 PowerShell/Windows Scheduled Tasks；Windows 包已做静态 adapter smoke，仍需要第一台 Windows 真机 DB smoke test。

## Windows smoke 证据

Windows runtime smoke 是开发/CI 验包流程，不放在用户可见发布包入口里。
