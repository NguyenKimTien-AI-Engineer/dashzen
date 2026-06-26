import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.main import create_app
from core.config import get_settings
from core.email.backend import set_email_backend_override
from core.email.testing import InMemoryEmailBackend
from db.base import Base
from db.session import get_db, reset_engine

# Test defaults — must be set before importing app settings
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32b!")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen",
)
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("EMAIL_BACKEND", "console")
os.environ.setdefault("AVATAR_STORAGE_DIR", "/tmp/dashzen-test-avatars")


async def _postgres_available() -> bool:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        await engine.dispose()


@pytest.fixture
def mail_backend() -> InMemoryEmailBackend:
    backend = InMemoryEmailBackend()
    set_email_backend_override(backend)
    yield backend
    set_email_backend_override(None)


@pytest.fixture
async def db_engine():
    if not await _postgres_available():
        pytest.skip("PostgreSQL not available — start docker compose")

    reset_engine()
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()
    reset_engine()


@pytest.fixture
async def client(db_engine, mail_backend):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
