from __future__ import annotations

import re

_STATUS_BLOCK_RE = re.compile(
    r"\*\*Status:\*\*\s*(DONE|WAIT|FAIL)\s*\n\s*\*\*Summary:\*\*\s*(.+?)(?:\n\s*\n|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def parse_agent_status_block(text: str) -> tuple[str, str] | None:
    """Return (status, summary) when the agent closed with the protocol block."""
    if not text.strip():
        return None
    match = _STATUS_BLOCK_RE.search(text.strip())
    if not match:
        return None
    return match.group(1).upper(), match.group(2).strip()


def format_agent_tool_result(status: str, summary: str) -> str:
    return f"**Status:** {status.upper()}\n**Summary:** {summary}"
