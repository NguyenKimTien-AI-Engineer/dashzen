#!/usr/bin/env bash
# Restart DashZen dev servers (API + Studio UI)
# Usage:
#   ./scripts/dev-restart.sh          # normal restart
#   ./scripts/dev-restart.sh --clean  # clear Next.js cache + restart

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CLEAN=false
if [[ "${1:-}" == "--clean" ]]; then
  CLEAN=true
fi

echo "==> Stopping API & Studio..."
pkill -f "uvicorn api.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
sleep 2

if [[ "$CLEAN" == true ]]; then
  echo "==> Clearing Next.js cache (.next)..."
  rm -rf apps/studio/.next
fi

if [[ ! -f .env ]]; then
  echo "WARN: .env not found — copy from .env.example"
fi

if [[ ! -f apps/studio/.env.local ]]; then
  echo "==> Creating apps/studio/.env.local from example..."
  cp apps/studio/.env.local.example apps/studio/.env.local
fi

if [[ ! -d .venv ]]; then
  echo "ERROR: .venv not found. Run: uv sync"
  exit 1
fi

echo "==> Starting API (http://localhost:8000)..."
.venv/bin/uvicorn api.main:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000 \
  --app-dir apps/api/src \
  > /tmp/dashzen-api.log 2>&1 &

echo "==> Starting Studio (http://localhost:3000)..."
(
  cd apps/studio
  npm run dev -- --port 3000
) > /tmp/dashzen-studio.log 2>&1 &

echo "==> Waiting for services..."
for i in {1..20}; do
  API_OK=false
  UI_OK=false
  curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1 && API_OK=true
  curl -sf -o /dev/null http://127.0.0.1:3000/login 2>/dev/null && UI_OK=true
  if [[ "$API_OK" == true && "$UI_OK" == true ]]; then
    break
  fi
  sleep 1
done

echo ""
if curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "✓ API:    http://localhost:8000  (docs: /docs)"
else
  echo "✗ API failed — tail /tmp/dashzen-api.log"
fi

if curl -sf -o /dev/null http://127.0.0.1:3000/login 2>/dev/null; then
  echo "✓ Studio: http://localhost:3000"
else
  echo "✗ Studio failed — tail /tmp/dashzen-studio.log"
fi

echo "  Mailpit: http://localhost:8025"
echo ""
echo "Logs:"
echo "  tail -f /tmp/dashzen-api.log"
echo "  tail -f /tmp/dashzen-studio.log"
