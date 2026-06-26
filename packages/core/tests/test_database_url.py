from core.database_url import database_url_for_async_engine, normalize_asyncpg_database_url


def test_strips_sslmode_for_asyncpg() -> None:
    raw = (
        "postgresql+asyncpg://user:pass@ep.example.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    url, connect_args = normalize_asyncpg_database_url(raw)
    assert "sslmode" not in url.query
    assert "channel_binding" not in url.query
    assert "ssl" in connect_args


def test_local_url_unchanged() -> None:
    raw = "postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen"
    url, connect_args = normalize_asyncpg_database_url(raw)
    assert str(url).startswith("postgresql+asyncpg://")
    assert connect_args == {}


def test_database_url_for_async_engine_returns_string() -> None:
    raw = "postgresql+asyncpg://u:p@host/db?sslmode=require"
    url_str, connect_args = database_url_for_async_engine(raw)
    assert "sslmode" not in url_str
    assert connect_args.get("ssl") is not None
