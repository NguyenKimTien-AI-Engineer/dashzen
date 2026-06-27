"""Health, readiness, and metrics endpoints."""
from __future__ import annotations

import time
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from api.monitoring.metrics import registry

log = structlog.get_logger()
router = APIRouter(tags=["observability"])

_START_TIME = time.time()


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Returns 200 as long as the process is alive."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready() -> dict[str, Any]:
    """Checks DB and Redis connectivity. Returns 503 if any dependency is unhealthy."""
    checks: dict[str, str] = {}
    healthy = True

    # DB check
    try:
        from db.session import get_session_factory

        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        log.error("readiness_db_fail", error=str(exc))
        checks["db"] = "error"
        healthy = False

    # Redis check
    try:
        import redis.asyncio as aioredis
        from core.config import get_settings

        settings = get_settings()
        if settings.redis_url:
            r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception as exc:
        log.error("readiness_redis_fail", error=str(exc))
        checks["redis"] = "error"
        healthy = False

    status = "ok" if healthy else "degraded"
    body: dict[str, Any] = {
        "status": status,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "checks": checks,
    }
    if not healthy:
        raise HTTPException(status_code=503, detail=body)
    return body


@router.get("/v1/metrics", summary="In-process metrics snapshot")
async def metrics() -> dict[str, Any]:
    """Returns a JSON snapshot of all in-process counters, gauges, and histograms."""
    return registry.snapshot()
