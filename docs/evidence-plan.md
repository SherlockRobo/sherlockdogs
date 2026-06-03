# Evidence Plan

Goal: support the Codex for OSS application without exposing private data.

## Safe Evidence

- Screenshot of Codex usage dashboard with account identifiers hidden.
- Monthly token usage aggregate, rounded.
- Count of local Sherlockdogs jobs processed.
- Count of generated clipping artifacts.
- Screenshot of Codex conversation list with private titles blurred or selectively cropped.
- Sample anonymized job JSON.
- Sample local archive tree with sensitive titles removed.

## Current Local Signals

- Processed job count: 47 done jobs in current dogfood queue.
- Local clipping tree: 67 item directories under current clipping scan.
- Dogfood artifacts size: 199M in local clipping, 14M in run logs.

## Redaction Rules

- Hide emails, org IDs, API keys, tokens, cookies, and local usernames.
- Do not include raw private chat messages.
- Do not include WeChat database paths.
- Do not include personal contact names.
- Do not publish screenshots containing private article titles unless approved.

