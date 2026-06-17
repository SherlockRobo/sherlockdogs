# Sherlockdogs Product Intro and Risk Disclosure

## 一句话

Sherlockdogs 是一个本地安全的 AI 剪藏管道：把微信文章、X 帖、小红书笔记、网页链接、图片、PDF、视频等线索，送进用户自己的本地资料库，并按需直接触发 Codex 对话。

```text
Sherlockdogs: everything to your Codex.
```

## 解决什么问题

| 痛点 | Sherlockdogs 做法 |
|---|---|
| 收藏分散在多个 App | 用统一 Inbox 接收链接和文件 |
| Obsidian 手动整理麻烦 | 后台自动生成 Markdown、metadata、assets |
| 想让 AI 继续处理 | `#2/#3/#4/#5` 直接创建 Codex 可见任务 |
| 不想把资料交给陌生服务 | 默认只用用户自己的电脑和同步盘 |
| 视频解析太重 | clipping 阶段只保存链接、封面、时长线索，深解析留给 Codex |

## 当前支持

| 类型 | 当前行为 |
|---|---|
| 微信公众号链接 | 保存原文结构、图片、metadata，支持后续精读 |
| X / Twitter 链接 | 保存公开 metadata、链接、标题和预览 |
| 小红书 / B站 / YouTube / 抖音 / TikTok 链接 | 保存链接、标题、封面或时长线索；不默认下载整视频 |
| 图片 | 复制到本地 assets，生成图片 clipping |
| PDF / 文本 / Markdown | 存入本地 clipping，保留原文件或原文 |
| Codex 对话 | `#2` 小卡片，`#3/#4/#5` 后续解析或深处理 |

## 指令等级

| 指令 | 行为 |
|---|---|
| 不写 / `#1` | 只入库 |
| `#` / `#2` | 入库并生成 Codex 小卡片 |
| `#3` | 在 Codex 里做简介、metadata、字幕优先解析 |
| `#4` / `#ob` | 在 Codex 里做精读或深处理 |
| `#5` | 在 Codex 里做关键帧、截图、拆段等重任务 |

## 默认数据流

```text
Mac:
手机微信发给自己
-> Mac 微信收到
-> Sherlockdogs Connect WeChat 读取本机 Mac 微信 DB
-> 本地 Markdown 图书馆
-> 可选 Codex 对话

Windows:
手机微信发给自己
-> Windows 微信收到
-> Sherlockdogs Connect WeChat 本地准备/读取 Windows 微信 DB
-> 本地 Markdown 图书馆
-> 可选 Codex 对话
```

## 使用到的开源组件

Sherlockdogs 自己负责本地编排、入库格式、Codex 任务触发和安装包。包内或安装流程会用到这些开源组件：

| 组件 | 用途 | 来源 |
|---|---|---|
| `requests` | HTTP 请求、公开页面 metadata 抓取 | `https://github.com/psf/requests` |
| `beautifulsoup4` | HTML 解析 | `https://www.crummy.com/software/BeautifulSoup/` |
| `markdownify` | HTML 转 Markdown | `https://github.com/matthewwithanm/python-markdownify` |
| `Pillow` | 图片处理、摘要图生成 | `https://github.com/python-pillow/Pillow` |
| `yt-dlp` | 视频链接 metadata、封面、时长线索 | `https://github.com/yt-dlp/yt-dlp` |
| `ffprobe` / FFmpeg | 本地视频时长和媒体信息读取，可选 | `https://ffmpeg.org/` |
| Python 标准库 | 文件监听、SQLite、JSON、subprocess、路径处理 | Python 标准库 |
| macOS `launchd` | Mac 用户态后台服务 | macOS 系统能力 |
| Windows Scheduled Tasks | Windows 用户态后台任务 | Windows 系统能力 |
| `zstandard` | 解压部分微信消息内容列 | `https://github.com/indygreg/python-zstandard` |

不属于 Sherlockdogs 打包内容、但用户可能会使用：

| 工具 | 作用 |
|---|---|
| iCloud / 坚果云 / OneDrive / Google Drive / Syncthing | 用户自己的手机到电脑同步 Inbox |
| Obsidian | 推荐的本地 Markdown 图书馆阅读器 |
| Codex | AI 对话和深处理执行入口 |

## 隐私边界

| 问题 | 当前设计 |
|---|---|
| Sherlockdogs 是否有云端服务器 | 默认没有 |
| 是否上传到 Sherlockdogs 中转 | 默认不上传 |
| 是否读取个人微信数据库 | Mac Personal Mode 需要用户主动运行 `Sherlockdogs Connect WeChat.app`；Windows 需要用户主动运行 `Sherlockdogs Connect WeChat.cmd`，本地准备/绑定 Windows 微信 DB |
| 同步盘是否能看到同步文件 | 如果用户选择 iCloud/坚果云/OneDrive/Google Drive 等，同步文件会进入用户自己的对应账号 |
| Codex 是否会收到内容 | 只有触发 Codex 任务时，相关内容会进入用户自己的 Codex/OpenAI 环境 |
| Obsidian 是否必需 | 不必需，输出本质是本地 Markdown 文件夹 |

## 风险披露

| 风险 | 说明 | 降低方式 |
|---|---|---|
| 同步盘风险 | iCloud、坚果云、OneDrive、Google Drive 或其他云盘会接触用户同步的 Inbox 文件 | 用户可改用本地文件夹、NAS、Syncthing 或其他自选同步方案 |
| Codex 隐私 | `#2/#3/#4/#5` 会把任务内容送入用户的 Codex 对话 | 敏感资料只用 `#1` 入库，或不要触发 AI 处理 |
| 平台反爬/风控 | 抓取公开网页 metadata、封面、时长时可能触发平台限流或失败 | 默认不绕过登录、不使用 cookies、不下载整视频；失败时保留链接 |
| 版权和平台条款 | 第三方内容归原平台和作者所有 | 只做个人资料管理，不做再分发 |
| 本地后台任务 | 安装后会创建用户态后台任务监听 Inbox | 可用卸载脚本移除；不需要 root |
| 文件误放 | 用户把敏感文件放进 Inbox 会被本地入库 | Inbox 只放想被整理的内容 |
| Windows 微信 DB | 当前已有 adapter 和本地 decrypt bootstrap，但仍需 Windows 真机验证 | 发布前做真实 Windows DB smoke，未通过前不标同款完成 |
| 依赖更新 | `yt-dlp`、平台页面结构、Python 包版本可能变化 | Doctor 诊断、版本固定、失败时保留原链接 |

## 当前不做

| 不做 | 原因 |
|---|---|
| 不提供 Sherlockdogs 云中转 | 保持“用户自己的资料只在自己的账户和电脑里” |
| 不内置云端微信中转 | 保持本地读取和用户自有数据边界 |
| 不默认下载整段视频 | 成本高、风险高、速度慢 |
| 不承诺绕过平台限制 | 只处理用户能正常访问的公开内容或本地文件 |
| 不替代 Obsidian | Obsidian 是推荐阅读器，不是运行硬依赖 |
