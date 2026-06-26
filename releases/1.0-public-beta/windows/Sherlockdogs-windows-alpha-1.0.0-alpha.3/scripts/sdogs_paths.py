#!/usr/bin/env python3
"""Shared path resolution for Sherlockdogs.

All public-beta paths are configurable through environment variables so the
same checkout can run on another Mac/Windows machine without bytedance-specific
absolute paths baked into the runtime.
"""

from __future__ import annotations

import os
from pathlib import Path


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default.expanduser()


PROJECT_DIR = env_path('SHERLOCKDOGS_PROJECT_DIR', Path(__file__).resolve().parents[1])
VAULT_DIR = env_path('SHERLOCKDOGS_VAULT_DIR', Path('~/ObsidianVault_LOCAL'))
CLIPPING_DIR = env_path('SHERLOCKDOGS_CLIPPING_DIR', VAULT_DIR / 'clipping')
INBOX_DIR = env_path('SHERLOCKDOGS_INBOX_DIR', Path('~/Sherlockdogs/Inbox'))
WORK_DIR = env_path('SHERLOCKDOGS_WORK_DIR', CLIPPING_DIR / '_sherlockdogs')
JOBS_DIR = WORK_DIR / 'jobs'
RUNS_DIR = WORK_DIR / 'runs'
