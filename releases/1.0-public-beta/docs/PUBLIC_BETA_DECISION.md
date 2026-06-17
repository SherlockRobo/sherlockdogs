# Sherlockdogs Public Beta Decision

Generated: 2026-06-16T19:49:57+0800

## Decision

| Scope | Status | Meaning |
|---|---|---|
| Mac public beta | READY | Mac release gate and runtime smoke on macOS |
| Windows package | NOT_READY | Current folder is only an Inbox/Shortcut experiment |
| Windows runtime | NOT_PARITY | Runtime smoke did not verify Windows WeChat DB capture |
| Mobile phone entry | VERIFIED | Requires real phone-to-desktop clipping evidence |
| Full public beta | NOT_READY | Windows must match the Mac WeChat DB path first |

## Machine Flags

```text
decision_status=MAC_READY_WINDOWS_DB_NOT_READY
mac_public_beta_ready=true
windows_package_ready=false
windows_runtime_verified=false
windows_runtime_evidence=<local-sherlockdogs-workdir>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt
mobile_entry_verified=true
mobile_entry_evidence=<local-sherlockdogs-workdir>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt
full_public_beta_ready=false
```

## Release Evidence

Current package is ready for macOS small public beta only. The Windows runtime evidence below only proves the old Inbox/Shortcut experiment; it does not prove Windows WeChat DB parity:

```text
windows_runtime_evidence=<local-sherlockdogs-workdir>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt
mobile_entry_evidence=<local-sherlockdogs-workdir>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt
```

Keep rerunning `packaging/public_beta_require_ready.sh` before sharing a refreshed package.

## Authoritative Files

- Build index: `dist/PUBLIC_BETA_INDEX.md`
- Readiness matrix: `dist/PUBLIC_BETA_READINESS.md`
- Share note: `dist/SHARE_PUBLIC_BETA.md`
