# Return Windows Evidence

Run this on the Windows test machine:

```text
Run Windows WeChat Smoke.cmd
```

It will print a one-time smoke text containing:

```text
https://example.com/sherlockdogs-windows-smoke
#2
sdogs-win-...
```

Send that exact text from phone WeChat to your own WeChat account. Wait until Windows WeChat shows the same token, then press Enter in the smoke window.

## Passing evidence

Return the latest report from:

```text
evidence\windows-wechat-db-smoke\
```

Easiest return path:

```text
Export Windows Evidence.cmd
```

This creates a Desktop folder named `Sherlockdogs-Windows-Evidence-*`. Send that folder back as-is. Do not zip it unless the operator explicitly asks for an archive.

The passing report must contain:

```text
token_match=ok
windows_wechat_db=ok
connect_wechat=ok
self_chat_received=ok
desktop_received=ok
codex_job_created=ok
codex_card=ok
thread_completed=True
receiver_chat=...
```

## If it fails

Return both:

```text
evidence\windows-wechat-db-smoke\
%USERPROFILE%\.sherlockdogs\diagnostics\doctor-*.txt
```

Or just run:

```text
Export Windows Evidence.cmd
```

The smoke command now keeps polling until timeout. If it still fails, it automatically runs Doctor and prints `diagnostic_report=...`.

Common failure meanings:

| Line | Meaning |
|---|---|
| `token_match=missing` | Windows DB did not surface this exact phone-sent token yet |
| `connect_wechat=missing` | Connect did not bind a usable decrypted Windows WeChat DB |
| `desktop_received=missing` | No matching Windows self-chat event was created |
| `codex_job_created=missing` | The message was seen, but did not produce a `#2` Codex job |
| `codex_card=missing` | A `#2` job exists, but Codex did not finish the card and move the job to done |
| `receiver_chat=...` missing | Receiver discovery did not learn the self-chat id |

## Build machine check

Back on the build machine, the Windows package is only Mac-like complete after real evidence contains:

```text
token_match=ok
windows_wechat_db=ok
codex_job_created=ok
codex_card=ok
thread_completed=True
```

Machine check:

```bash
./check_returned_windows_evidence.sh /path/to/Sherlockdogs-Windows-Evidence-*
```
