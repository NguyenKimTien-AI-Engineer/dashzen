# Deploy (PaaS Option 3) — Vercel + Render + Neon

Production deploy uses **platform Git integration**, not this workflow alone.

| Layer | Service | Config in repo |
|-------|---------|----------------|
| Studio | [Vercel](https://vercel.com) | `apps/studio/vercel.json`, `pages/api/[...path].ts` |
| API | [Render](https://render.com) | `Dockerfile`, `render.yaml` |
| Database | [Neon](https://neon.tech) | `DATABASE_URL` in Render env |
| LLM | Gemini / OpenRouter | API env vars |
| CD smoke | GitHub Actions | `.github/workflows/cd.yml` |

## Quick checklist

1. **Neon** — create project → connection string with `postgresql+asyncpg://` and `?sslmode=require`
2. **Render** — New Blueprint → select repo → set env from `.env.example`
3. **Vercel** — Import repo → Root Directory: `apps/studio` → env below
4. **Merge to `main`** — Vercel + Render auto-deploy

## Auth architecture (same-origin proxy)

Studio and API run on different hosts in production, but the **browser only talks to Vercel**:

```
Browser → https://your-app.vercel.app/api/v1/auth/login
              ↓  pages/api/[...path].ts (serverless proxy)
          https://dashzen-api.onrender.com/v1/auth/login
```

Auth cookies are **first-party** on the Vercel domain → works on mobile Safari/Android.

### Vercel env (Production)

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `/api` |
| `API_BACKEND_URL` | `https://dashzen-api.onrender.com` |

Do **not** set `NEXT_PUBLIC_API_URL` to the Render URL in production.

### Render env

| Variable | Value |
|----------|--------|
| `REFRESH_COOKIE_PATH` | `/api/v1/auth` |
| `COOKIE_SAMESITE` | `lax` |
| `COOKIE_SECURE` | `true` |
| `API_CORS_ORIGINS` | optional (browser uses same-origin `/api`) |

Also: `DATABASE_URL`, `JWT_SECRET_KEY`, `API_PUBLIC_URL`, `GEMINI_API_KEY`.

### Local dev

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` |

No proxy locally — Studio `:3000` calls API `:8000` directly with `COOKIE_SAMESITE=lax`.

## Render (API)

```bash
docker build -t dashzen-api .
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e JWT_SECRET_KEY="your-32-char-minimum-secret" \
  -e REFRESH_COOKIE_PATH=/api/v1/auth \
  -e COOKIE_SAMESITE=lax \
  -e COOKIE_SECURE=true \
  -e API_PUBLIC_URL="http://localhost:8000" \
  -e LLM_PROVIDER=gemini \
  -e GEMINI_API_KEY="..." \
  dashzen-api
```

Migrations run automatically on container start (`scripts/start-api.sh`).

## Vercel (Studio)

**Important:** import the repo with **Root Directory = `apps/studio`**.

Project settings:

- **Root Directory:** `apps/studio` (required)
- **Framework:** Next.js (auto-detected)
- **Environment:** see auth table above

Preview deployments: use the same `NEXT_PUBLIC_API_URL=/api` + production `API_BACKEND_URL`, or a staging API URL.

## GitHub CD

After CI passes on `main`, **CD** workflow (`.github/workflows/cd.yml`):

- Optional repository **variables:** `API_HEALTH_URL`, `STUDIO_URL`
- Optional **secret:** `RENDER_DEPLOY_HOOK_URL`

## Free tier limits

- Render free sleeps after ~15 min idle (cold start)
- SSE agent streams through Vercel proxy may hit timeout on free tier
- Avatar files on Render disk are **ephemeral** — use object storage for production

## Manual migration (without Docker)

```bash
export DATABASE_URL="postgresql+asyncpg://..."
./scripts/migrate.sh
uv run --package api uvicorn api.main:app --host 0.0.0.0 --port 8000
```
