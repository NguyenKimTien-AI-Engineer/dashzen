"""Sanitize model thinking for user-visible Thinking panel.

Strips internal # MEMORY / # WORKFLOW blocks and redacts paths, phases, and tool
names. Benign LLM reasoning is preserved — never replaced with hardcoded copy.
"""

from __future__ import annotations

import re

_HASH_SECTION = re.compile(
    r"^#+\s*(MEMORY|WORKFLOW|CONTEXT|TOOLS)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
_INTERNAL_FILE = re.compile(
    r"\b[\w./-]+\.(?:md|json|yaml|yml|csv)\b",
    re.IGNORECASE,
)
_WORKFLOW_PHASE = re.compile(
    r"\b(?:create-chat|create-dashboard|edit-dashboard|repair-dashboard)\b",
    re.IGNORECASE,
)
_LEAK_MARKERS = re.compile(
    r"memory\.md|workflow/|system-main\.md|user_instructions",
    re.IGNORECASE,
)
_TOOL_NAMES = re.compile(
    r"\b(?:spawn_agent|set_memory|read_file|write_file|list_file)\b",
    re.IGNORECASE,
)
_INTERNAL_LINE = re.compile(
    r"^(phase|type|step)\s*:",
    re.IGNORECASE,
)


def _strip_internal_sections(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _HASH_SECTION.match(line):
            index += 1
            while index < len(lines):
                inner = lines[index]
                if _HASH_SECTION.match(inner):
                    break
                if not inner.strip():
                    index += 1
                    continue
                if _INTERNAL_LINE.match(inner.strip()):
                    index += 1
                    continue
                if _WORKFLOW_PHASE.search(inner) or _INTERNAL_FILE.search(inner):
                    index += 1
                    continue
                break
            continue
        kept.append(line)
        index += 1
    return "\n".join(kept)


def sanitize_thinking_for_display(text: str) -> str:
    """Return redacted thinking safe for the Thinking panel."""
    if not text or not text.strip():
        return ""

    out = _strip_internal_sections(text)
    out = _HASH_SECTION.sub("", out)
    out = _INTERNAL_FILE.sub("[file]", out)
    out = _WORKFLOW_PHASE.sub("[workflow]", out)
    out = _TOOL_NAMES.sub("[tool]", out)

    lines = [line for line in out.splitlines() if line.strip() and not _LEAK_MARKERS.search(line)]
    out = "\n".join(lines).strip()
    out = re.sub(r"\n{3,}", "\n\n", out).strip()

    if not out:
        return ""

    return out[:8000]
