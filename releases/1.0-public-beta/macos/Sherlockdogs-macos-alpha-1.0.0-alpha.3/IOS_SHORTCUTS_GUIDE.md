# iOS Shortcut: Send to Sherlockdogs

## 核心结论

快捷指令做的事很简单：

```text
任意 App 分享内容
-> iOS 快捷指令
-> 生成一个 txt 文件
-> 保存到用户自己选择的 Inbox
-> 电脑端 Sherlockdogs 自动处理
```

Sherlockdogs 不需要读微信数据库，也不需要用户把内容发给第三方账号。

## 发布包里已经给了什么

发布包包含一个可导入的快捷指令种子文件：

```text
shortcuts/Send-to-Sherlockdogs-Inbox.shortcut
```

它解决的是“用户怎么有这个入口”的问题：用户不用从零搭快捷指令，可以先导入这个文件，在分享面板里看到“发送到 Sherlockdogs”，并把内容保存到自己选择的 Inbox。

当前种子文件会在每次运行时询问保存位置。公开版最终应把它通过 Shortcuts 分享成 iCloud 安装链接：

```text
https://www.icloud.com/shortcuts/<id>
```

这样用户只需要点链接、添加快捷指令。Apple 要求 iCloud 分享动作生成这个链接，不能用普通文件路径伪造。

## 用户第一次要选什么

快捷指令不是把同步方式和目录写死。用户第一次配置时选两件事：

| 选择项 | 推荐默认 | 可以改成 |
|---|---|---|
| 同步通道 | 坚果云 WebDAV | iCloud Drive、OneDrive、Google Drive、Syncthing、NAS、本地文件夹 |
| Inbox 目录 | `Sherlockdogs/Inbox` | 用户自己的任意同步目录，比如 `AIInbox`、`Clippings/Sherlockdogs` |

之后日常使用不再选择目录，只在分享时选处理级别 `#1/#2/#3/#4/#5`。

## 你现在怎么测

如果电脑不能用 iCloud，就不要走 iCloud 版。测试路径改成：

```text
iPhone 分享内容
-> 发送到 Sherlockdogs 快捷指令
-> 用户选择的同步通道，当前建议坚果云 WebDAV
-> 电脑同步到用户选择的本地 Inbox
-> Sherlockdogs 自动入库/进 Codex
```

这条路径不要求电脑登录 iCloud，也不要求 Sherlockdogs 读微信数据库。

你只需要确认三件事：

| 项 | 要做什么 |
|---|---|
| 手机 | 快捷指令用用户选择的同步通道上传 txt |
| 电脑 | 同步客户端已登录，并同步用户选择的 Inbox |
| Sherlockdogs | Inbox 指向电脑本地同一个 Inbox |

## 版本选择

| 版本 | 适合谁 | 同步方式 | 配置难度 |
|---|---|---|---|
| 坚果云版 | 中国区、Windows/Mac 混用、电脑不能用 iCloud 的用户 | Nutstore WebDAV | 中等 |
| iCloud 版 | Mac/iPhone 同账号用户 | iCloud Drive | 最低 |
| 文件夹版 | 桌面手动测试 | 本地 Inbox | 最低 |

## 当前 MVP 支持

| 内容 | 状态 | 说明 |
|---|---|---|
| 链接 | 已支持 | 微信文章、网页、X、小红书、B站、YouTube、抖音等链接 |
| 文字 | 已支持 | 保存为 txt/md |
| 指令 | 已支持 | `#1/#2/#3/#4/#5` |
| 图片/文件 | 可入库 | 直接保存文件，默认按 `#1` 处理 |
| 图片/文件带指令 | 下一版 | 用 dated bundle：`task.txt + assets` |

## 快捷指令 A：坚果云 WebDAV 版

适合 Windows/Mac 混用，或电脑不能用 iCloud 的用户。

### 前置

1. 坚果云开启 WebDAV。
2. 创建应用密码。
3. 选择一个 Inbox 目录。推荐默认：

```text
https://dav.jianguoyun.com/dav/Sherlockdogs/Inbox/
```

也可以换成用户自己的路径，例如：

```text
https://dav.jianguoyun.com/dav/AIInbox/
https://dav.jianguoyun.com/dav/Clippings/Sherlockdogs/
```

手机快捷指令里的 WebDAV 目标路径，必须和电脑端 Sherlockdogs 监听的本地同步目录对应。

不要把坚果云登录密码写进快捷指令。使用坚果云应用密码。

### 快捷指令动作

新建快捷指令，命名：

```text
发送到 Sherlockdogs
```

打开快捷指令详情：

```text
在共享表单中显示：开启
接收类型：文本、URL、网页、图片、文件、PDF、媒体
```

动作顺序：

| 步骤 | 快捷指令动作 | 设置 |
|---|---|---|
| 1 | 文本 | 用户选择的 WebDAV Inbox 基础路径，例如 `https://dav.jianguoyun.com/dav/Sherlockdogs/Inbox` |
| 2 | 设定变量 | 变量名 `InboxBaseUrl` |
| 3 | 从菜单中选取 | `#1 只入库`、`#2 入库+Codex卡片`、`#3 摘要`、`#4 精读`、`#5 视频关键帧` |
| 4 | 设定变量 | 变量名 `Command`，值为菜单对应的 `#1/#2/#3/#4/#5` |
| 5 | 当前日期 | 无 |
| 6 | 格式化日期 | 自定义格式 `yyyyMMdd-HHmmss` |
| 7 | 文本 | `快捷指令输入` + 空行 + `Command` |
| 8 | 文本 | `坚果云邮箱:坚果云应用密码` |
| 9 | Base64 编码 | 编码上一步文本 |
| 10 | 获取 URL 内容 | 见下面设置 |

`获取 URL 内容` 设置：

```text
URL:
InboxBaseUrl/sdogs-格式化日期.txt

方法:
PUT

请求体:
第 7 步生成的文本

Headers:
Authorization: Basic 第 9 步 Base64 结果
Content-Type: text/plain; charset=utf-8
```

成功后，Mac/Windows 坚果云会同步这个 txt 文件，Sherlockdogs 自动入库。

## 快捷指令 B：iCloud Drive 版

适合 Apple 全家桶用户。优点是不需要 WebDAV 密码。

### 前置

1. iPhone 打开 iCloud Drive。
2. 选择或创建一个 Inbox 目录。推荐默认：

```text
Sherlockdogs/Inbox
```

也可以换成用户自己的目录，例如：

```text
AIInbox
Clippings/Sherlockdogs
```

3. Mac 端 Sherlockdogs 的 Inbox 指到同一个 iCloud Drive 目录。

### 快捷指令动作

新建快捷指令，命名：

```text
发送到 Sherlockdogs
```

打开快捷指令详情：

```text
在共享表单中显示：开启
接收类型：文本、URL、网页、图片、文件、PDF、媒体
```

动作顺序：

| 步骤 | 快捷指令动作 | 设置 |
|---|---|---|
| 1 | 从菜单中选取 | `#1 只入库`、`#2 入库+Codex卡片`、`#3 摘要`、`#4 精读`、`#5 视频关键帧` |
| 2 | 设定变量 | 变量名 `Command`，值为菜单对应的 `#1/#2/#3/#4/#5` |
| 3 | 当前日期 | 无 |
| 4 | 格式化日期 | 自定义格式 `yyyyMMdd-HHmmss` |
| 5 | 文本 | 见下面模板 |
| 6 | 存储文件 | 关闭“询问存储位置”，路径为用户选择的 iCloud Inbox，例如 `iCloud Drive/Sherlockdogs/Inbox/sdogs-格式化日期.txt` |

文本动作模板：

```text
快捷指令输入

Command
```

实际保存出来应该像这样：

```text
https://mp.weixin.qq.com/s/xxxx

#2
```

## 指令规则

| 指令 | 行为 |
|---|---|
| 空白或 `#1` | 只入库 |
| `#2` 或 `#` | 入库并生成 Codex 小卡片 |
| `#3` | 轻解析、摘要、metadata |
| `#4` 或 `#ob` | 精读、深处理 |
| `#5` | 视频关键帧、截图、拆段 |

## 测试用例

分享任意网页到快捷指令，选择 `#2`。桌面端应该收到一个文件：

```text
<用户选择的 Inbox>/sdogs-YYYYMMDD-HHMMSS.txt
```

文件内容类似：

```text
https://example.com

#2
```

如果桌面 Sherlockdogs 正在运行，30 秒内应该入库；`#2` 会尝试生成 Codex 小卡片。

## 常见问题

| 问题 | 处理 |
|---|---|
| 分享面板看不到快捷指令 | 打开快捷指令详情，确认“在共享表单中显示”已开启 |
| iCloud 版没同步到 Mac | 确认 Mac 和 iPhone 是同一个 Apple ID，且 iCloud Drive 已开启 |
| 坚果云版 401 | 应用密码或邮箱错误，不要用普通登录密码 |
| 坚果云版 404 | 先在坚果云创建用户选择的 Inbox 目录 |
| Codex 没弹卡片 | 先确认文件已入库；`#2` 之后还需要 Codex 本机可用 |
