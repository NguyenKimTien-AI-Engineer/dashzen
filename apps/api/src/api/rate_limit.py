from functools import wraps
from typing import Any, Callable, TypeVar

from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import get_settings

limiter = Limiter(key_func=get_remote_address)

F = TypeVar("F", bound=Callable[..., Any])


def rate_limit(limit_value: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        limited = limiter.limit(limit_value)(func)

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if get_settings().rate_limit_enabled:
                return await limited(*args, **kwargs)
            return await func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
