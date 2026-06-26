from __future__ import annotations

import json
from typing import Any


def encode_thinking(data: dict[str, Any] | list[Any]) -> str:
    return json.dumps(data)


def decode_thinking(s: str | None) -> dict[str, Any] | list[Any] | None:
    if not s:
        return None
    try:
        parsed = json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(parsed, (dict, list)):
        return parsed
    return None
