#!/usr/bin/env bash
# Start infrastructure: PostgreSQL + Mailpit
# Usage: ./scripts/dev-infra.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Starting Docker services (postgres + mailpit)..."
docker compose -f infra/compose/docker-compose.yml up -d

echo "==> Running migrations..."
.venv/bin/alembic -c packages/db/alembic.ini upgrade head

echo ""
echo "✓ Postgres: localhost:5432"
echo "✓ Mailpit:  http://localhost:8025  (SMTP :1025)"
