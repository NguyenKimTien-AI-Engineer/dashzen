from __future__ import annotations

import time

import redis.asyncio as aioredis
from core.config import get_settings

BUCKET_LIMITS: dict[str, tuple[int, int]] = {
    "task_stream": (100, 3600),
    "task_create": (30, 3600),
    "upload": (30, 3600),
}

_mem_buckets: dict[str, tuple[float, int]] = {}


async def _get_redis() -> aioredis.Redis | None:  # type: ignore[type-arg]
    try:
        r = aioredis.from_url(get_settings().redis_url, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


async def check_rate_limit(bucket: str, key: str, limit: int, window_sec: int) -> bool:
    """Token bucket rate limit check. Returns True if request is allowed."""
    redis_key = f"ratelimit:{bucket}:{key}"
    now = time.time()

    redis = await _get_redis()
    if redis is not None:
        lua = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local data = redis.call("HMGET", key, "tokens", "last")
        local tokens = tonumber(data[1])
        local last = tonumber(data[2])
        if tokens == nil then
            tokens = limit
            last = now
        else
            local elapsed = now - last
            local refill = math.floor(elapsed / window * limit)
            if refill > 0 then
                tokens = math.min(limit, tokens + refill)
                last = now
            end
        end
        if tokens <= 0 then
            redis.call("HMSET", key, "tokens", 0, "last", last)
            redis.call("EXPIRE", key, window)
            return 0
        end
        tokens = tokens - 1
        redis.call("HMSET", key, "tokens", tokens, "last", last)
        redis.call("EXPIRE", key, window)
        return 1
        """
        allowed = await redis.eval(lua, 1, redis_key, limit, window_sec, now)  # type: ignore[attr-defined]
        await redis.aclose()
        return bool(allowed)

    state = _mem_buckets.get(redis_key)
    if state is None:
        _mem_buckets[redis_key] = (now, limit - 1)
        return True

    last, tokens = state
    elapsed = now - last
    if elapsed >= window_sec:
        tokens = limit
        last = now

    if tokens <= 0:
        _mem_buckets[redis_key] = (last, 0)
        return False

    _mem_buckets[redis_key] = (last, tokens - 1)
    return True


def get_bucket_config(bucket: str) -> tuple[int, int]:
    return BUCKET_LIMITS.get(bucket, (100, 3600))


async def retry_after_seconds(bucket: str, key: str, window_sec: int) -> int:
    redis_key = f"ratelimit:{bucket}:{key}"
    redis = await _get_redis()
    if redis is not None:
        ttl = await redis.ttl(redis_key)
        await redis.aclose()
        return max(1, int(ttl)) if ttl and ttl > 0 else window_sec
    return window_sec
