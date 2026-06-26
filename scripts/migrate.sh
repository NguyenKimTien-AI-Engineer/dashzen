#!/usr/bin/env bash
# Apply Alembic migrations (production / CI / Docker).
# Usage: ./scripts/migrate.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

uv run alembic -c packages/db/alembic.ini upgrade head
