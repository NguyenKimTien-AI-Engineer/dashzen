from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from core.config import get_settings

_LOCK_TTL_SEC = 90
_LOCK_REFRESH_INTERVAL_SEC = 20.0
_LOCK_KEY_PREFIX = "lock:stream:"

_mem_locks: dict[str, str] = {}


class StreamLockError(Exception):
    pass


async def _get_redis() -> aioredis.Redis | None:  # type: ignore[type-arg]
    try:
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


class StreamLock:
    def __init__(self, task_id: str) -> None:
        self._key = f"{_LOCK_KEY_PREFIX}{task_id}"
        self._token = str(uuid.uuid4())
        self._redis: aioredis.Redis | None = None  # type: ignore[type-arg]
        self._heartbeat_task: asyncio.Task | None = None  # type: ignore[type-arg]

    async def acquire(self) -> None:
        self._redis = await _get_redis()
        if self._redis is not None:
            ok = await self._redis.set(self._key, self._token, nx=True, ex=_LOCK_TTL_SEC)
            if not ok:
                raise StreamLockError("Task is already being processed")
        else:
            if self._key in _mem_locks:
                raise StreamLockError("Task is already being processed")
            _mem_locks[self._key] = self._token
        self._heartbeat_task = asyncio.create_task(self._heartbeat())

    async def release(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
        if self._redis is not None:
            lua = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            end
            return 0
            """
            await self._redis.eval(lua, 1, self._key, self._token)  # type: ignore[attr-defined]
            await self._redis.aclose()
        else:
            if _mem_locks.get(self._key) == self._token:
                _mem_locks.pop(self._key, None)

    async def _heartbeat(self) -> None:
        while True:
            await asyncio.sleep(_LOCK_REFRESH_INTERVAL_SEC)
            try:
                if self._redis is not None:
                    current = await self._redis.get(self._key)
                    if current == self._token:
                        await self._redis.expire(self._key, _LOCK_TTL_SEC)
            except Exception:
                pass


@contextlib.asynccontextmanager
async def stream_lock(task_id: str) -> AsyncGenerator[None, None]:
    lock = StreamLock(str(task_id))
    await lock.acquire()
    try:
        yield
    finally:
        await lock.release()
