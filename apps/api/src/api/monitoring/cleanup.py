"""Background cleanup task — runs periodically to prune old file versions."""
from __future__ import annotations

import asyncio

import structlog
from db.services.file_service import cleanup_old_file_versions
from db.session import get_session_factory
from sqlalchemy import text

from api.monitoring.metrics import record_cleanup_run

log = structlog.get_logger()

_CLEANUP_INTERVAL_SEC = 6 * 3600  # every 6 hours
_KEEP_VERSIONS = 10


async def _run_cleanup_once() -> None:
    session_factory = get_session_factory()
    total_deleted = 0
    try:
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT DISTINCT task_id FROM files WHERE is_current = false")
            )
            task_ids = [row[0] for row in result]

        for task_id in task_ids:
            async with session_factory() as session:
                try:
                    deleted = await cleanup_old_file_versions(
                        session, task_id, keep_versions=_KEEP_VERSIONS
                    )
                    await session.commit()
                    total_deleted += deleted
                except Exception:
                    await session.rollback()
                    log.exception("cleanup_task_error", task_id=str(task_id))

        record_cleanup_run(deleted=total_deleted)
        if total_deleted:
            log.info("cleanup_complete", deleted_versions=total_deleted)
    except Exception:
        log.exception("cleanup_run_error")


async def run_cleanup_loop() -> None:
    """Long-running coroutine — meant to be started in FastAPI lifespan."""
    await asyncio.sleep(60)  # brief startup delay
    while True:
        await _run_cleanup_once()
        await asyncio.sleep(_CLEANUP_INTERVAL_SEC)
