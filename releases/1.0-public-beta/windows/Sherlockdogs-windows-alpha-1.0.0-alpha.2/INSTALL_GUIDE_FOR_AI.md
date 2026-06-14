---
title: Sherlockdogs AI 安装说明
date: 2026-06-11
status: active
audience: ai-support
---

# Sherlockdogs AI 安装说明

【核心结论】

给 Mac 用户只讲四件事：打开 Sherlockdogs，点 `Connect WeChat`，手机转发一条测试内容给自己的微信，之后继续转发给自己即可。Inbox/Shortcut 是兜底路径。坚果云是中国区同步兜底方案，但不是硬依赖；Obsidian 推荐但不强制；Codex 需要本机已安装或可用。

## 用户最短步骤

| 步骤 | Mac | Windows |
|---|---|---|
| 1 | 可选：安装并登录坚果云/iCloud 等同步盘 | 可选：安装并登录坚果云/OneDrive 等同步盘 |
| 2 | 双击 `Sherlockdogs Start.app` | 双击 `Sherlockdogs Start.cmd` |
| 3 | 双击 `Sherlockdogs Connect WeChat.app`，按提示发测试消息给自己 | 本地用默认 Inbox；坚果云用户双击 `Configure Nutstore Inbox.cmd` |
| 4 | 以后手机转发任意内容给自己的微信 | 手机用快捷指令/同步盘保存到 `/Sherlockdogs/Inbox` |
| 5 | 双击 `Sherlockdogs Open Output.app` 查看结果 | 双击 `Open Sherlockdogs Output.cmd` 查看结果 |

## 指令规则

| 指令 | 行为 |
|---|---|
| 空白或 `#1` | 只入库，写本地 Markdown |
| `#2` 或 `#` | 入库，并生成 Codex 小卡片 |
| `#3` | 轻解析元数据和简介 |
| `#4` | 深度阅读或精读 |
| `#5` | 视频关键帧、截图、拆段 |

## 给用户的解释

Mac 最佳路径是“转发给自己的微信”。用户运行 `Sherlockdogs Connect WeChat.app` 后，Sherlockdogs 会读取本机 Mac 微信数据来自动绑定这个自聊会话。它不需要把内容发给 Sherlockdogs 官方账号。Inbox/Shortcut 仍作为兜底路径。

Obsidian 是本地 Markdown 图书馆阅读器。没有 Obsidian 也能保存文件；装了 Obsidian 会更方便浏览和搜索。

Codex 是任务处理入口。只有 `#2/#3/#4/#5` 这类指令需要进入 Codex；纯 `#1` 只保存。

## 常见问题

| 问题 | 回答 |
|---|---|
| 没装 Obsidian 能不能用 | 能，文件会保存到 `~/Sherlockdogs/Vault/clipping` 或 Windows 对应目录 |
| 内容会不会上传到 Sherlockdogs | 默认不会，云同步使用用户自己的 iCloud/坚果云/OneDrive/Google Drive/Syncthing 等账号 |
| 电脑关了会不会处理 | 不会，电脑端 Sherlockdogs 和 Mac 微信需要运行 |
| 手机怎么投递 | Mac 推荐转发给自己微信；兜底用快捷指令或同步盘 `/Sherlockdogs/Inbox` |
| 找不到结果 | 运行 Doctor，再打开 Output 或 Diagnostics |

## 支持口径

如果用户说“没反应”，按这个顺序排查：

1. Mac 微信是否登录，聊天列表里是否能看到刚转发给自己的内容。
2. 是否运行过 `Sherlockdogs Connect WeChat.app`。
3. 运行 `scripts/wechat_doctor.py --lookback-seconds 3600 --show 10` 看是否能读到最近消息。
4. 兜底路径再看同步盘是否已登录并同步，或本地 Inbox 是否存在。
5. 运行 `Doctor Sherlockdogs` 并查看诊断报告。
