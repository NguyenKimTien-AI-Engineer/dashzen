from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_PATH_SEPARATORS = re.compile(r"[/\\]|\.\./|\.\.\\")


def has_path_separator(value: str) -> bool:
    """Return True if value contains path traversal or separator characters."""
    return bool(_PATH_SEPARATORS.search(value))


def sanitize_filename(name: str) -> str:
    """Strip control chars, null bytes, and path separators from a filename."""
    cleaned = _CONTROL_CHARS.sub("", name).replace("\x00", "")
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    cleaned = cleaned.replace("..", "_")
    cleaned = cleaned.strip().strip(".")
    return cleaned or "upload"
