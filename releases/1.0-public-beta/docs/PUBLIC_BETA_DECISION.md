# Sherlockdogs Public Beta Decision

Generated: 2026-06-16T19:49:57+0800

## Decision

| Scope | Status | Meaning |
|---|---|---|
| Mac public beta | READY | Mac release gate and runtime smoke on macOS |
| Windows package | ASSEMBLED | Windows release folder and static gate |
| Windows runtime | VERIFIED | Requires real Windows machine or GitHub Actions runner |
| Mobile phone entry | VERIFIED | Requires real phone-to-desktop clipping evidence |
| Full public beta | READY | Desktop, Windows runtime, and phone entry verified |

## Machine Flags

```text
decision_status=READY_FOR_PUBLIC_BETA
mac_public_beta_ready=true
windows_package_ready=true
windows_runtime_verified=true
windows_runtime_evidence=<local-sherlockdogs-workdir>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt
mobile_entry_verified=true
mobile_entry_evidence=<local-sherlockdogs-workdir>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt
full_public_beta_ready=true
```

## Release Evidence

Current package is ready for small public beta. Windows runtime and mobile entry evidence are already present:

```text
windows_runtime_evidence=<local-sherlockdogs-workdir>/dist/evidence/windows-runtime-smoke/runtime-smoke-b885c8355f71.txt
mobile_entry_evidence=<local-sherlockdogs-workdir>/dist/evidence/mobile-entry-smoke/20260604-105632-wechat-inbox-bc01a246c6.txt
```

Keep rerunning `packaging/public_beta_require_ready.sh` before sharing a refreshed package.

## Authoritative Files

- Build index: `dist/PUBLIC_BETA_INDEX.md`
- Readiness matrix: `dist/PUBLIC_BETA_READINESS.md`
- Share note: `dist/SHARE_PUBLIC_BETA.md`
