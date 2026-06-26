import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from core.config import get_settings
from db.base import Base
from db.models.agent_run import AgentRun  # noqa: F401
from db.models.email_verification import EmailVerificationCode  # noqa: F401
from db.models.file import File  # noqa: F401
from db.models.message import Message  # noqa: F401
from db.models.project import Project  # noqa: F401
from db.models.refresh_token import RefreshToken  # noqa: F401
from db.models.task import Task  # noqa: F401
from db.models.user import User  # noqa: F401
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure repo-root .env is loaded when running from packages/db
_repo_root = Path(__file__).resolve().parents[3]
_env_file = _repo_root / ".env"
if _env_file.is_file():
    import os

    for line in _env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())

target_metadata = Base.metadata
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
