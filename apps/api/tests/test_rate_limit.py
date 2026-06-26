import os

import pytest
from api.main import create_app
from core.config import get_settings
from db.base import Base
from db.session import get_db, reset_engine
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def rate_limited_client(monkeypatch: pytest.MonkeyPatch):
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set")

    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()

    reset_engine()
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL not available — start docker compose")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
    reset_engine()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(rate_limited_client: AsyncClient) -> None:
    email = "nobody@example.com"
    password = "wrongpass1"

    for _ in range(5):
        res = await rate_limited_client.post(
            "/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert res.status_code == 401

    blocked = await rate_limited_client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert blocked.status_code == 429


@pytest.mark.asyncio
async def test_register_rate_limit_returns_429(rate_limited_client: AsyncClient) -> None:
    for i in range(10):
        res = await rate_limited_client.post(
            "/v1/auth/register",
            json={"email": f"ratelimit-{i}@example.com", "password": "securepass123"},
        )
        assert res.status_code == 201

    blocked = await rate_limited_client.post(
        "/v1/auth/register",
        json={"email": "ratelimit-blocked@example.com", "password": "securepass123"},
    )
    assert blocked.status_code == 429
