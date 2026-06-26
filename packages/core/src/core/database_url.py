"""PostgreSQL URL helpers for SQLAlchemy + asyncpg."""

from __future__ import annotations

import ssl
from typing import Any

from sqlalchemy.engine import URL, make_url

# libpq query params that asyncpg.connect() does not accept (Neon adds these).
_LIBPQ_ONLY_QUERY_KEYS = frozenset(
    {
        "sslmode",
        "channel_binding",
        "options",
        "gssencmode",
        "target_session_attrs",
    }
)

_SSLMODE_REQUIRES_TLS = frozenset({"require", "verify-ca", "verify-full", "prefer"})


def _ensure_asyncpg_driver(url: URL) -> URL:
    """Neon gives postgresql:// — DashZen requires asyncpg, not psycopg2."""
    if url.drivername == "postgresql":
        return url.set(drivername="postgresql+asyncpg")
    return url


def normalize_asyncpg_database_url(database_url: str) -> tuple[URL, dict[str, Any]]:
    """Strip libpq-only query params and map sslmode to asyncpg connect_args."""
    url = _ensure_asyncpg_driver(make_url(database_url))
    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    for key in _LIBPQ_ONLY_QUERY_KEYS:
        query.pop(key, None)

    connect_args: dict[str, Any] = {}
    if sslmode is not None:
        mode = sslmode.lower()
        if mode in _SSLMODE_REQUIRES_TLS:
            connect_args["ssl"] = ssl.create_default_context()
        elif mode == "disable":
            connect_args["ssl"] = False

    return url.set(query=query), connect_args


def database_url_for_async_engine(database_url: str) -> tuple[str, dict[str, Any]]:
    """String URL + connect_args for create_async_engine."""
    url, connect_args = normalize_asyncpg_database_url(database_url)
    return url.render_as_string(hide_password=False), connect_args
