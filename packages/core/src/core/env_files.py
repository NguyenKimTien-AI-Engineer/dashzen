"""Resolve and load repo / PaaS env files into os.environ."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    # packages/core/src/core/env_files.py → repo root
    return Path(__file__).resolve().parents[4]


def env_file_candidates() -> list[Path]:
    root = repo_root()
    return [
        root / ".env",
        root / ".env.production",
        Path("/etc/secrets/.env"),
        Path("/etc/secrets/.env.production"),
    ]


def resolve_env_files() -> list[Path]:
    return [path for path in env_file_candidates() if path.is_file()]


def _parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    return key.strip(), value.strip()


def load_env_files() -> list[Path]:
    """Load env files with setdefault so real OS env vars (Render dashboard) win."""
    loaded: list[Path] = []
    for path in resolve_env_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_env_line(line)
            if parsed is not None:
                os.environ.setdefault(*parsed)
        loaded.append(path)
    return loaded
