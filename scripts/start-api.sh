#!/usr/bin/env bash
# Production API entrypoint: migrate DB then start uvicorn.
# Render/Fly set PORT; default 8000 for local Docker.
# Docker image has .venv only (no uv binary) — use venv tools directly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${PORT:-8000}"

run_migrate() {
  if command -v uv >/dev/null 2>&1; then
    (cd packages/db && uv run alembic upgrade head)
  else
    (cd packages/db && alembic upgrade head)
  fi
}

run_api() {
  if command -v uv >/dev/null 2>&1; then
    exec uv run --package api uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
  else
    exec uvicorn api.main:app --host 0.0.0.0 --port "$PORT"
  fi
}

echo "==> Running database migrations..."
run_migrate

echo "==> Starting API on 0.0.0.0:${PORT}..."
run_api
