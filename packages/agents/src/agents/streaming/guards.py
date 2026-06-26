from __future__ import annotations

import asyncio
import hashlib
import time
from collections import deque

_DEDUP_WINDOW_SEC = 5.0
_DEDUP_MAX_SIZE = 500

_dedup_cache: deque[tuple[str, str, float]] = deque(maxlen=_DEDUP_MAX_SIZE)

_abort_signals: dict[str, asyncio.Event] = {}


def get_or_create_abort_signal(task_id: str) -> asyncio.Event:
    if task_id not in _abort_signals:
        _abort_signals[task_id] = asyncio.Event()
    return _abort_signals[task_id]


def clear_abort_signal(task_id: str) -> None:
    _abort_signals.pop(task_id, None)


def is_duplicate_request(task_id: str, content: str) -> bool:
    h = hashlib.sha256(content.encode()).hexdigest()
    now = time.monotonic()
    for tid, ch, ts in _dedup_cache:
        if tid == task_id and ch == h and (now - ts) < _DEDUP_WINDOW_SEC:
            return True
    _dedup_cache.append((task_id, h, now))
    return False
