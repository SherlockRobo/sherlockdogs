# Examples

These examples mirror real Sherlockdogs workflows without exposing private logs.

## WeChat Article

```text
https://mp.weixin.qq.com/s/example
#4
```

Expected behavior:

- Archive raw link and metadata to `clipping/wechat/`.
- Create a deep-reading Codex task.

## X Post

```text
Interesting market structure thread
https://x.com/example/status/123
#2
```

Expected behavior:

- Archive link and context to `clipping/x/`.
- Create a Codex card with the title/context.

## Video Link

```text
https://www.youtube.com/watch?v=dQw4w9WgXcQ
#3
```

Expected behavior:

- Archive link to `clipping/youtube/`.
- Prepare a lightweight metadata/transcript task.
- Defer expensive frame extraction until explicitly requested.

## Mixed Bundle

```text
Research this positioning angle.
https://example.com/article
Screenshot attached in local inbox.
#2
```

Expected behavior:

- Save the text and link together.
- Preserve the original bundle shape.
- Create a compact Codex task.

