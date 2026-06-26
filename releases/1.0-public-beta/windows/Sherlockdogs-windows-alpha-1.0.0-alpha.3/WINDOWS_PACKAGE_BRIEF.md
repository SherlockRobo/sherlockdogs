# Sherlockdogs Windows Package Brief

## 核心结论

Windows 测试包正在补齐 Mac 同款产品路径：手机微信发给自己，Windows 微信收到，Sherlockdogs 读取本机 Windows 微信 DB 并入库。当前包已包含 Windows WeChat DB adapter、Connect 入口和本地 decrypt bootstrap；边界是真 Windows 机器还必须跑完整 self-chat smoke。

## 包信息

| 项目 | 内容 |
|---|---|
| 平台 | Windows |
| 版本 | `1.0.0-alpha.3` |
| 包目录 | `Sherlockdogs-windows-alpha-1.0.0-alpha.3` |
| 当前大小 | `564K`，以当前 release 目录 `du -sh` 实测 |
| 默认入口 | `Sherlockdogs Start.cmd` |
| 微信入口 | `Sherlockdogs Connect WeChat.cmd` + 本地 decrypt bootstrap / 已解密 Windows 微信 DB |
| 可选配置入口 | `Configure Nutstore Inbox.cmd` |
| 诊断入口 | `Doctor Sherlockdogs.cmd` |
| 一键求助 | `OneClick Codex Help.cmd` |
| 输出入口 | `Open Sherlockdogs Output.cmd` |

## 用户使用

1. 打开 `INSTALL_GUIDE_FOR_USERS.png`。
2. 双击 `Sherlockdogs Start.cmd`。
3. 保持 Windows 微信登录。
4. 双击 `Sherlockdogs Connect WeChat.cmd`；它会绑定已有解密 DB，或尝试本地 decrypt bootstrap。
5. 手机微信发一条测试内容给自己；Windows 微信收到后，Sherlockdogs 从本地 DB 入库。
6. 用 `Open Sherlockdogs Output.cmd` 查看结果。
7. 跑 `Run Windows WeChat Smoke.cmd` 做完整真机向导，或跑 `Collect Windows WeChat Evidence.cmd` 生成 smoke 证据。

## 系统改动

| 改动 | 说明 |
|---|---|
| 用户配置 | 写入 `%USERPROFILE%\.sherlockdogs\config.ps1` |
| Python 环境 | 创建或复用 `%USERPROFILE%\.sherlockdogs\venv` |
| 后台服务 | 创建当前用户的 Windows Scheduled Tasks，包括 `SherlockdogsWindowsWeChatInbox` |
| 本地输出 | 写入用户配置的 clipping 目录 |
| 卸载 | `Uninstall Sherlockdogs.cmd` 只卸载后台任务，不删除用户内容 |

## 包内主要文件

| 文件 | 用途 |
|---|---|
| `INSTALL_GUIDE_FOR_USERS.png` | 给用户看的图形安装说明 |
| `INSTALL_GUIDE_FOR_AI.md` | 给 AI/客服看的安装说明 |
| `Sherlockdogs Connect WeChat.cmd` | 准备/绑定 Windows 微信 DB 目录 |
| `Run Windows WeChat Smoke.cmd` | 真机完整路径 smoke 向导 |
| `Collect Windows WeChat Evidence.cmd` | 生成 Windows WeChat DB smoke 证据 |
| `PRODUCT_INTRO_AND_RISK_DISCLOSURE.md` | 产品介绍、依赖、风险披露 |
| `START_HERE.md` | 用户第一步说明 |
| `README.md` | 完整 Windows 测试包说明 |
| `TROUBLESHOOTING.md` | 常见问题 |
| `CHECKSUMS.txt` | 包内文件校验 |

## 当前边界

Windows 包已通过本机静态 release gate 和模拟 decrypted DB adapter smoke。正式标成 Mac 同款前，还必须在真实 Windows 机器上验证：取 key / 解密 -> `Sherlockdogs Connect WeChat.cmd` -> 微信自聊消息入库 -> Codex 卡片 -> `Run Windows WeChat Smoke.cmd` 或 `Collect Windows WeChat Evidence.cmd` 产出 PASS。
