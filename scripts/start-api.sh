#!/usr/bin/env bash
# Production API entrypoint: migrate DB then start uvicorn.
# Render/Fly set PORT; default 8000 for local Docker.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"

echo "==> Running database migrations..."
(cd packages/db && uv run alembic upgrade head)

echo "==> Starting API on 0.0.0.0:${PORT}..."
exec uv run --package api uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
