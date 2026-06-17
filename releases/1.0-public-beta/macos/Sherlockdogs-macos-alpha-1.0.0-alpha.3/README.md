# Sherlockdogs Mac Alpha 小范围测试包

目标：陌生 Mac 用户不用把内容交给 Sherlockdogs 云端。测试版的推荐入口是手机微信转发给自己；Inbox/Shortcut/同步盘只是兜底传输层。电脑端收到后在本机入库，并按 `#1/#2/#3/#4/#5` 触发 Codex 对话。

Obsidian 是推荐阅读器，但不是硬依赖。Sherlockdogs 输出的是本地 Markdown 图书馆；不装 Obsidian 也能保存文件并触发 Codex，对 Obsidian 用户则能直接沉淀到 vault。

## 推荐入口：微信转发给自己

1. 先双击 `Sherlockdogs Start.app`，让电脑端保持运行。
2. 双击 `Sherlockdogs Connect WeChat.app`。
3. 手机微信转发一条测试内容给自己的微信号；Mac 微信必须收到。
4. Mac 端读取本机微信数据后，Sherlockdogs 自动入库并生成本地 Markdown / Codex 任务。
5. Inbox/Shortcut/同步盘仍可作为兜底路径，但不是推荐入口。

## 默认入口

- Inbox：`~/Sherlockdogs/Inbox`
- 输出：`~/ObsidianVault_LOCAL/clipping/`，如果没有这个 Vault，则使用 `~/Sherlockdogs/Vault/clipping/`
- 配置：`~/.sherlockdogs/config.env`
- Python venv：`~/.sherlockdogs/venv`

## 双击入口

普通用户只需要这些入口：

- `Sherlockdogs Start.app`：推荐入口，安装 + 生成诊断报告
- `Configure Nutstore Inbox.command`：可选兜底，把 Inbox 切换到用户自己的同步目录
- `Sherlockdogs Doctor.app`：推荐诊断入口
- `Sherlockdogs Open Output.app`：推荐结果查看入口
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

推荐把内容通过微信转发给自己；快捷指令/同步盘/Inbox 只是兜底传输层。桌面手动测试时，也可以把以下内容放进当前 Sherlockdogs Inbox：

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

- 默认公测入口是手机分享链接或微信转发给自己；Inbox/同步盘只是后台传输层，不读取个人微信数据库。
- 推荐用 Obsidian 打开本地 Markdown 图书馆，但不强制安装 Obsidian。
- “转发给自己微信”属于高级本机适配器，需要用户的 Mac 微信处于可读状态，暂不作为公测默认路径。
- Sherlockdogs 不上传用户剪藏内容到 Sherlockdogs 中转服务；同步盘内容属于用户自己的账号，电脑同步后在本机进入 Codex。
