# Sherlockdogs Mac Alpha 小范围测试包

目标：陌生 Mac 用户不用把内容交给 Sherlockdogs 云端。测试版主入口是手机微信转发给自己；Mac 微信收到后，用户主动运行 `Sherlockdogs Connect WeChat.app` 才会读取本机 Mac 微信数据，随后在本机入库，并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。iOS Shortcut、iCloud、坚果云、OneDrive、Google Drive、Syncthing、NAS、本地 Inbox 都只是兜底入口。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：微信转发给自己

1. 先双击 `Sherlockdogs Start.app`，让电脑端保持运行。
2. 双击 `Sherlockdogs Connect WeChat.app`，按提示用手机微信转发一条测试内容给自己。
3. 以后从微信、网页、X、小红书、PDF、图片等入口，把线索转发给自己的微信。
4. Mac 微信收到后，Sherlockdogs 自动入库并生成本地 Markdown；用 `Sherlockdogs Open Output.app` 查看结果。
5. 如果新发内容没进来，先双击 `Sherlockdogs OneTouchRepair.app`；需要看诊断再双击 `Sherlockdogs Doctor.app`。

## 兜底入口：Inbox / 同步盘

如果 Mac 微信路径不可用，再用 iOS 快捷指令 / 同步盘承接手机内容，并选择自己的后台传输目录：iCloud、坚果云、OneDrive、Google Drive、Syncthing 或 NAS。

坚果云用户可双击 `Configure Nutstore Inbox.command` 自动检测同步目录，并创建：

```text
<坚果云同步目录>/Sherlockdogs/Inbox
<坚果云同步目录>/Sherlockdogs/Outbox
```

Mac 端收到后台传输文件后，Sherlockdogs 同样会自动入库并生成本地 Markdown。

## 默认入口

- Inbox：`~/Sherlockdogs/Inbox`
- 输出：`~/ObsidianVault_LOCAL/clipping/`，如果没有这个 Vault，则使用 `~/Sherlockdogs/Vault/clipping/`
- 配置：`~/.sherlockdogs/config.env`
- Python venv：`~/.sherlockdogs/venv`

## 双击入口

普通用户只需要这些入口：

- `Sherlockdogs Start.app`：一键启动，安装 + 生成诊断报告
- `Sherlockdogs Connect WeChat.app`：主入口，连接 Mac 微信自聊路径
- `Sherlockdogs Open Output.app`：推荐结果查看入口
- `Sherlockdogs OneTouchRepair.app`：一键修复，重启服务、修复微信绑定、追补扫描
- `Sherlockdogs Doctor.app`：推荐诊断入口
- `Configure Nutstore Inbox.command`：可选，把 Inbox 切换到用户自己的坚果云同步目录
- `Uninstall Sherlockdogs.command`：卸载后台服务
- `INSTALL_GUIDE_FOR_USERS.png`：给用户看的图形安装说明
- `INSTALL_GUIDE_FOR_USERS.svg`：可编辑图源
- `INSTALL_GUIDE_FOR_AI.md`：给 AI/客服看的安装说明

## 命令行安装

```bash
./packaging/macos-beta/install.sh
```

安装会自动创建 venv 并安装 `requirements.txt` 里的依赖。安装后启动两个用户态 LaunchAgent：

- `com.sherlockdogs.local-inbox`：监听 Inbox，生成任务
- `com.sherlockdogs.codex-runner`：消费任务并打开/触发 Codex 对话

开发/验证时可用：

```bash
./packaging/macos-beta/install.sh --no-load --skip-deps
```

## 使用

推荐把内容通过手机微信转发给自己；快捷指令/同步盘/Inbox 只是兜底入口。桌面手动测试时，也可以把以下内容放进当前 Sherlockdogs Inbox：

- `.txt/.md/.url/.webloc`：里面包含微信、X、小红书、B站、YouTube、抖音、TikTok 链接
- 图片：`.jpg/.png/.webp/.gif/.heic`
- 视频文件：`.mp4/.mov/.m4v/.webm`
- PDF：`.pdf`

指令规则：

- 不写或 `#1`：只入库
- `#` 或 `#2`：入库，并生成 Codex 小卡片
- `#3`：做简介/元数据解析
- `#4` 或 `#ob`：做精读
- `#5`：做关键帧、截图、拆段

## 诊断

```bash
./packaging/macos-beta/doctor.sh
```

会输出路径、LaunchAgent 状态、队列数量、Python 包、`yt-dlp`、`ffprobe`、Codex 可执行文件和最近错误。

## 自测

```bash
./packaging/macos-beta/selftest.sh
./packaging/macos-beta/release_check.sh
```

自测只使用 `/tmp` 临时目录，不启动后台服务，不写入真实 Vault。`release_check.sh --with-deps` 会额外真实安装依赖，适合发版前使用。

## macOS 打不开时

如果 macOS 提示 `.app` 或 `.command` 无法打开：

1. 先右键 `Sherlockdogs Start.app`，选择 Open，再确认 Open。
2. 如果仍失败，在包目录打开 Terminal，执行：

```bash
xattr -dr com.apple.quarantine .
chmod +x "Configure Nutstore Inbox.command" "Uninstall Sherlockdogs.command"
```

3. 再双击 `Sherlockdogs Start.app`。

## 发布目录

```bash
./packaging/macos-beta/build_release_folder.sh
```

发布目录会生成到 `dist/macos-beta/Sherlockdogs-macos-alpha-<version>/`。按当前规则不生成 zip/dmg；给测试用户时直接给这个文件夹。

## 卸载

```bash
./packaging/macos-beta/uninstall.sh
```

只卸载后台服务，不删除 Inbox、Vault、配置和已入库内容。

## 公测边界

- 默认公测入口是手机微信转发给自己；只有用户主动运行 `Sherlockdogs Connect WeChat.app` 后，才读取本机 Mac 微信数据。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- Inbox/Shortcut/同步盘是兜底入口；同步盘内容属于用户自己的账号，电脑同步后在本机进入 Codex。
- Sherlockdogs 不上传用户剪藏内容到 Sherlockdogs 中转服务。
