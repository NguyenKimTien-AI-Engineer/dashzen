# Deploy (PaaS Option 3) — Vercel + Render + Neon

Production deploy uses **platform Git integration**, not this workflow alone.

| Layer | Service | Config in repo |
|-------|---------|----------------|
| Studio | [Vercel](https://vercel.com) | `apps/studio/vercel.json` |
| API | [Render](https://render.com) | `Dockerfile`, `render.yaml` |
| Database | [Neon](https://neon.tech) | `DATABASE_URL` in Render env |
| LLM | Gemini / OpenRouter | API env vars |
| CD smoke | GitHub Actions | `.github/workflows/cd.yml` |

## Quick checklist

1. **Neon** — create project → connection string with `postgresql+asyncpg://` and `?sslmode=require`
2. **Render** — New Blueprint → select repo → set env from `.env.production.example`
3. **Vercel** — Import repo → Root Directory: `apps/studio` → `NEXT_PUBLIC_API_URL`
4. **Merge to `main`** — Vercel + Render auto-deploy; CD workflow runs smoke if variables set

## Render (API)

```bash
# Local Docker parity
docker build -t dashzen-api .
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e JWT_SECRET_KEY="your-32-char-minimum-secret" \
  -e API_CORS_ORIGINS="http://localhost:3000" \
  -e API_PUBLIC_URL="http://localhost:8000" \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY="..." \
  dashzen-api
```

Required Render env vars (see `.env.production.example`):

- `DATABASE_URL`, `JWT_SECRET_KEY`, `API_CORS_ORIGINS`, `API_PUBLIC_URL`, `GEMINI_API_KEY`
- `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none` for cross-domain auth

Migrations run automatically on container start (`scripts/start-api.sh`).

## Vercel (Studio)

Project settings:

- **Root Directory:** `apps/studio`
- **Framework:** Next.js (auto-detected)
- **Environment:** `NEXT_PUBLIC_API_URL` = Render API URL (Production)

Preview deployments: set `NEXT_PUBLIC_API_URL` to a staging API or the same production API.

## GitHub CD

After CI passes on `main`, **CD** workflow (`.github/workflows/cd.yml`):

- Prints deploy status when smoke URLs are not configured
- Optional repository **variables:**
  - `API_HEALTH_URL` — e.g. `https://dashzen-api.onrender.com/health`
  - `STUDIO_URL` — e.g. `https://your-app.vercel.app`
- Optional **secret:** `RENDER_DEPLOY_HOOK_URL` — manual workflow dispatch to trigger Render

## Free tier limits

- Render free sleeps after ~15 min idle (cold start)
- SSE agent streams may hit proxy timeouts on free tiers
- Avatar files on Render disk are **ephemeral** — use object storage for production
- Gemini/OpenRouter free quotas exhaust quickly with multi-agent runs

## Manual migration (without Docker)

```bash
export DATABASE_URL="postgresql+asyncpg://..."
./scripts/migrate.sh
uv run --package api uvicorn api.main:app --host 0.0.0.0 --port 8000
```
