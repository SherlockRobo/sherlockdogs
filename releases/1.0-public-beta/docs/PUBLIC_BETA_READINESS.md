# Sherlockdogs Public Beta Readiness

Generated: 2026-06-17T18:26:33+0800

## Status

| Item | Status | Evidence |
|---|---|---|
| macOS release folder | PASS | `<release-root>/dist/macos-beta/Sherlockdogs-macos-alpha-1.0.0-alpha.3` |
| macOS runtime smoke | PASS | `packaging/macos-beta/release_check.sh` |
| Windows release folder | PASS | `<release-root>/dist/windows-beta/Sherlockdogs-windows-alpha-1.0.0-alpha.2` |
| Windows static gate | PASS | `packaging/windows-beta/release_check.sh` |
| Windows runtime smoke | PASS | <release-root>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt |
| Windows WeChat DB smoke | PENDING | Needs real Windows WeChat DB parity smoke |
| Mobile phone entry smoke | PASS | <release-root>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt |
| Windows automated smoke script | PASS | source/CI only, not user-facing release entry |
| Windows CI smoke template | PASS | `dist/ci/windows-runtime-smoke.yml` included |
| Windows GitHub Actions workflow | PASS | `.github/workflows/windows-runtime-smoke.yml` included |
| Windows WeChat DB simulated CI template | PASS | `dist/ci/windows-wechat-db-sim-smoke.yml` included |
| Windows WeChat DB simulated workflow | PASS | `.github/workflows/windows-wechat-db-sim-smoke.yml` included |
| Public repo Windows release smoke template | PASS | `dist/ci/public-windows-release-smoke.yml` included |
| No archive output | PASS | Release policy and dist scan |
| Primary phone WeChat entry | PASS | Mac uses Connect WeChat; Windows includes Connect WeChat DB adapter/bootstrap |
| Optional Inbox fallback | PASS | Nutstore/local folder configuration entry included, but not the primary product path |
| Local privacy boundary | PASS | WeChat DB modes are opt-in and local-only; release folders include no Sherlockdogs relay services |
| User self-help entries | PASS | Start, Configure, Output, Doctor, Uninstall, picture guide included |
| Preflight check | PASS | Python, Codex, network, write permission, ffprobe checks run inside Start |

## Public beta decision

Mac desktop package is ready for direct folder sharing after the macOS rows are PASS. Sherlockdogs 1.0 public-beta readiness is decided by the table above and `dist/PUBLIC_BETA_DECISION.md`. Preferred Mac mobile evidence is WeChat self-chat -> Mac -> Sherlockdogs -> Codex card; Shortcut/Inbox evidence is accepted as fallback.

Windows public beta package is assembled and statically gated. It is Mac-equivalent only when the Windows WeChat DB smoke row above is PASS.

Full 1.0 public beta is READY only when Windows WeChat DB smoke and Mobile phone entry smoke are PASS.

If the project is pushed to GitHub, run `.github/workflows/windows-runtime-smoke.yml` and `.github/workflows/windows-wechat-db-sim-smoke.yml` from Actions.

## Windows smoke acceptance

On a clean Windows user account:

1. Double-click `Sherlockdogs Start.cmd`.
2. Keep Windows WeChat logged in.
3. Run `Sherlockdogs Connect WeChat.cmd`; it should prepare or bind local Windows WeChat DBs containing `message\message_*.db`.
4. Forward one real `#2` phone WeChat item to yourself and confirm Windows WeChat receives it.
5. Confirm Sherlockdogs creates local Markdown and a Codex card.
6. Run `Run Windows WeChat Smoke.cmd` for the guided flow, or `Collect Windows WeChat Evidence.cmd` if the test item was already sent. Copy the generated PASS report into `dist/evidence/windows-wechat-db-smoke/`.
7. The report must contain `windows_wechat_db=ok`, `connect_wechat=ok`, `self_chat_received=ok`, `desktop_received=ok`, `codex_job_created=ok`, `codex_card=ok`, and `thread_completed=True`.
