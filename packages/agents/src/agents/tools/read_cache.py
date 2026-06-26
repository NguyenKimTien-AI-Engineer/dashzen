from __future__ import annotations

import json


class ReadCache:
    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def _key(self, tool_name: str, args: dict) -> str:  # type: ignore[type-arg]
        return f"{tool_name}:{json.dumps(args, sort_keys=True)}"

    def get(self, tool_name: str, args: dict) -> str | None:  # type: ignore[type-arg]
        return self._cache.get(self._key(tool_name, args))

    def set(self, tool_name: str, args: dict, result: str) -> None:  # type: ignore[type-arg]
        self._cache[self._key(tool_name, args)] = result

    def invalidate_path(self, path: str) -> None:
        keys_to_drop = [k for k in self._cache if path in k]
        for k in keys_to_drop:
            self._cache.pop(k, None)

    def invalidate_workspace_listing(self) -> None:
        """Drop cached list_file results after workspace files change."""
        keys_to_drop = [k for k in self._cache if k.startswith("list_file:")]
        for k in keys_to_drop:
            self._cache.pop(k, None)

    def clear(self) -> None:
        self._cache.clear()
