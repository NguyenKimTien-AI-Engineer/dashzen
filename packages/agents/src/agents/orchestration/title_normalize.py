"""Normalize LLM-generated task titles before persisting or displaying."""

from __future__ import annotations

import re

_MARKDOWN_WRAPPER = re.compile(r"^[*_`]+|[*_`]+$")
_INLINE_MARKDOWN = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__|`([^`]+)`")


def normalize_task_title(raw: str) -> str | None:
    title = raw.strip().strip('"').strip("'")
    title = _MARKDOWN_WRAPPER.sub("", title)
    title = _INLINE_MARKDOWN.sub(lambda m: m.group(1) or m.group(2) or m.group(3) or "", title)
    title = re.sub(r"\s+", " ", title).strip()
    if not title or title.lower() == "null":
        return None
    # Reject titles too short to be meaningful (avoids single-letter glitches like "Đ").
    if len(title) < 3:
        return None
    return title[:255]
