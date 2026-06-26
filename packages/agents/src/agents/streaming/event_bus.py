from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from pydantic import BaseModel

from agents.streaming.events import serialize_sse

_SENTINEL = object()


class EventBus:
    def __init__(self, maxsize: int = 1000) -> None:
        self._queue: asyncio.Queue[object] = asyncio.Queue(maxsize=maxsize)

    def emit(self, event: BaseModel) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # drop if consumer is too slow

    def close(self) -> None:
        self._queue.put_nowait(_SENTINEL)

    async def __aiter__(self) -> AsyncGenerator[str, None]:
        while True:
            item = await self._queue.get()
            if item is _SENTINEL:
                return
            if isinstance(item, BaseModel):
                yield serialize_sse(item)
