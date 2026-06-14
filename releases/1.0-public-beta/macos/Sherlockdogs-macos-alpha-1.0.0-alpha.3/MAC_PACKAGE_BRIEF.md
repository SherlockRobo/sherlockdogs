# Sherlockdogs Mac Package Brief

## 核心结论

Mac 测试包是给普通用户双击运行的本地版 Sherlockdogs。1.0 主路径是 `Sherlockdogs Connect WeChat.app`：用户手机把内容转发给自己的微信，Mac 微信收到后，本机读取并进入 Codex。Inbox/Shortcut 作为兜底路径；不使用 Sherlockdogs 云中转。

## 包信息

| 项目 | 内容 |
|---|---|
| 平台 | macOS |
| 版本 | `1.0.0-alpha.3` |
| 包目录 | `Sherlockdogs-macos-alpha-1.0.0-alpha.3` |
| 当前大小 | `636K`，以当前 release 目录 `du -sh` 实测 |
| 默认入口 | `Sherlockdogs Start.app` |
| 配置入口 | `Configure Nutstore Inbox.command` |
| 微信入口 | `Sherlockdogs Connect WeChat.app` |
| 诊断入口 | `Sherlockdogs Doctor.app` |
| 输出入口 | `Sherlockdogs Open Output.app` |

## 用户使用

1. 可选：安装并登录坚果云 Mac 客户端，或准备 iCloud Drive 等自选同步目录。
2. 打开 `INSTALL_GUIDE_FOR_USERS.png`。
3. 双击 `Sherlockdogs Start.app`。
4. 双击 `Sherlockdogs Connect WeChat.app`，按提示用手机微信转发一条测试内容给自己。
5. 以后手机把链接、图片、PDF、视频、文本转发给自己的微信。
6. 兜底：坚果云用户双击 `Configure Nutstore Inbox.command`，绑定自己的 `Sherlockdogs/Inbox`。
7. Mac 收到后自动入库；用 `Sherlockdogs Open Output.app` 查看结果。

## 系统改动

| 改动 | 说明 |
|---|---|
| 用户配置 | 写入 `~/.sherlockdogs/config.env` |
| Python 环境 | 创建或复用 `~/.sherlockdogs/venv` |
| 后台服务 | 创建用户态 LaunchAgent，不需要 root |
| 微信模式 | 可选创建 `com.sherlockdogs.wechat-self`，读取本机 Mac 微信数据 |
| 本地输出 | 写入用户配置的 clipping 目录 |
| 卸载 | `Uninstall Sherlockdogs.command` 只卸载后台服务，不删除用户内容 |

## 包内主要文件

| 文件 | 用途 |
|---|---|
| `INSTALL_GUIDE_FOR_USERS.png` | 给用户看的图形安装说明 |
| `INSTALL_GUIDE_FOR_AI.md` | 给 AI/客服看的安装说明 |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | 产品介绍、依赖、风险披露 |
| `START_HERE.md` | 用户第一步说明 |
| `README.md` | 完整 Mac 测试包说明 |
| `TROUBLESHOOTING.md` | 常见问题 |
| `CHECKSUMS.txt` | 包内文件校验 |
