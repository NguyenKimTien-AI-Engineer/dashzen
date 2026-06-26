from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass

_WARN_THRESHOLD = 3
_BLOCK_THRESHOLD = 5
_WINDOW_SIZE = 20


@dataclass
class _CallRecord:
    key: str
    count: int = 1


class LoopDetector:
    def __init__(self) -> None:
        self._window: deque[str] = deque(maxlen=_WINDOW_SIZE)
        self._counts: dict[str, int] = {}

    def _make_key(self, tool_name: str, args: dict) -> str:  # type: ignore[type-arg]
        return f"{tool_name}:{json.dumps(args, sort_keys=True)}"

    def check(self, tool_name: str, args: dict) -> tuple[bool, str | None]:  # type: ignore[type-arg]
        """Returns (should_block, warning_message_or_None)."""
        key = self._make_key(tool_name, args)
        self._counts[key] = self._counts.get(key, 0) + 1
        self._window.append(key)
        count = self._counts[key]
        if count >= _BLOCK_THRESHOLD:
            return True, (
                f"[Loop detected] Tool '{tool_name}' called {count} times"
                " with identical args. Blocked."
            )
        if count >= _WARN_THRESHOLD:
            return False, (
                f"[Loop warning] Tool '{tool_name}' called {count} times with identical args."
            )
        return False, None

    def reset(self) -> None:
        self._window.clear()
        self._counts.clear()
