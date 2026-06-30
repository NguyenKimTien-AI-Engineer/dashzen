#!/usr/bin/env bash
# Apply Alembic migrations (production / CI / Docker).
# Usage: ./scripts/migrate.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v uv >/dev/null 2>&1; then
  uv run python -c "from core.env_files import load_env_files; load_env_files()"
else
  python -c "from core.env_files import load_env_files; load_env_files()"
fi

(cd packages/db && uv run alembic upgrade head)
