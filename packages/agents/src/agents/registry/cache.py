from __future__ import annotations

import os
from typing import TypeVar

T = TypeVar("T")

_mtime_cache: dict[str, tuple[float, object]] = {}


def get_cached(path: str, loader: object) -> object | None:
    if not callable(loader):
        return None
    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        return None
    if path in _mtime_cache:
        cached_mtime, value = _mtime_cache[path]
        if mtime <= cached_mtime:
            return value
    value = loader(path)
    _mtime_cache[path] = (mtime, value)
    return value


def invalidate(path: str) -> None:
    _mtime_cache.pop(path, None)
