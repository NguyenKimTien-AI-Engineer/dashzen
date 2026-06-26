from __future__ import annotations

from agents.streaming.rate_limit import check_rate_limit, get_bucket_config, retry_after_seconds
from db.models.user import User
from fastapi import Depends, HTTPException

from api.deps import get_current_user


def _rate_limit_headers(limit: int, retry_after: int) -> dict[str, str]:
    return {
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": "0",
    }


async def enforce_task_stream_limit(user: User = Depends(get_current_user)) -> User:
    limit, window = get_bucket_config("task_stream")
    if not await check_rate_limit("task_stream", str(user.id), limit, window):
        retry = await retry_after_seconds("task_stream", str(user.id), window)
        raise HTTPException(
            status_code=429,
            detail="Stream rate limit exceeded",
            headers=_rate_limit_headers(limit, retry),
        )
    return user


async def enforce_task_create_limit(user: User = Depends(get_current_user)) -> User:
    limit, window = get_bucket_config("task_create")
    if not await check_rate_limit("task_create", str(user.id), limit, window):
        retry = await retry_after_seconds("task_create", str(user.id), window)
        raise HTTPException(
            status_code=429,
            detail="Task creation rate limit exceeded",
            headers=_rate_limit_headers(limit, retry),
        )
    return user
