# Sherlockdogs Public Beta Decision

Generated: 2026-06-17T12:16:18+0800

## Decision

| Scope | Status | Meaning |
|---|---|---|
| Mac public beta | READY | Mac release gate and runtime smoke on macOS |
| Windows package | ASSEMBLED | Windows release folder and static gate |
| Windows runtime | VERIFIED | Old runtime smoke only; not parity proof |
| Windows WeChat DB | PENDING | Requires real Windows WeChat DB self-chat smoke |
| Mobile phone entry | VERIFIED | Requires real phone-to-desktop clipping evidence |
| Full public beta | NOT READY | Mac path, Windows DB path, and phone entry verified |

## Machine Flags

```text
decision_status=NEEDS_WINDOWS_WECHAT_DB_SMOKE
mac_public_beta_ready=true
windows_package_ready=true
windows_runtime_verified=true
windows_runtime_evidence=<release-root>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt
windows_wechat_db_verified=false
windows_wechat_db_evidence=missing
mobile_entry_verified=true
mobile_entry_evidence=<release-root>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt
full_public_beta_ready=false
```

## Next Required Evidence

To move from `NEEDS_WINDOWS_WECHAT_DB_SMOKE` to `READY_FOR_PUBLIC_BETA`, run a real Windows WeChat DB parity smoke. The report must be placed in `dist/evidence/windows-wechat-db-smoke/` or `evidence/windows-wechat-db-smoke/` and include `windows_wechat_db=ok`, `connect_wechat=ok`, `self_chat_received=ok`, `desktop_received=ok`, and `codex_card=ok`.

## Authoritative Files

- Build index: `dist/PUBLIC_BETA_INDEX.md`
- Readiness matrix: `dist/PUBLIC_BETA_READINESS.md`
- Share note: `dist/SHARE_PUBLIC_BETA.md`
