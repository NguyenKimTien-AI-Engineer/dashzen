# DashZen

Multi-agent system that turns natural-language requests into deployable dashboard pages.

## Architecture

- **Backend:** Python 3.12+ / FastAPI — self-built agent runtime (11 subsystems)
- **Studio UI:** Next.js 15 — chat-first web app with live canvas preview
- **Monorepo:** `uv` workspace (Python) + `apps/studio` (Node)

```
dashzen/
├── apps/
│   ├── api/          # FastAPI — REST + SSE adapter
│   └── studio/       # Next.js — chat + canvas
├── packages/
│   ├── core/         # LLM, schemas, config
│   ├── agents/       # Agent runtime subsystems
│   ├── tools/        # Tool implementations
│   ├── db/           # Persistence models
│   ├── rag/          # Vector store (catalog)
│   └── eval/         # Golden test sets
├── plan/             # Architecture & phase specs
├── templates/        # Widget templates for codegen
├── generated/        # Agent output sandbox (gitignored)
└── infra/            # Docker Compose & deployment
```

## Documentation

| Doc | Description |
|-----|-------------|
| [plan/01-project-structure-and-techstack.md](plan/01-project-structure-and-techstack.md) | System-of-systems architecture |
| [plan/02-ui-features-chat-agent.md](plan/02-ui-features-chat-agent.md) | Studio UI/UX spec |
| [plan/phases/Backend/](plan/phases/Backend/) | Backend implementation phases |
| [plan/phases/UI/UX/](plan/phases/UI/UX/) | Frontend implementation phases |

## Quick start (coming soon)

```bash
# Infrastructure
docker compose -f infra/compose/docker-compose.yml up -d

# Backend
cp .env.example .env
uv sync
uv run --package api uvicorn api.main:app --reload

# Studio
cd apps/studio
cp .env.local.example .env.local
npm install
npm run dev   # http://localhost:3000
```

## CI/CD

GitHub Actions workflows (`.github/workflows/`):

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | PR + push `main`/`develop` | Ruff, pytest (Postgres), Studio vitest + build |
| **E2E** | Weekly + manual + Studio PRs | Playwright public smoke |
| **CD** | After CI on `main` + manual | Post-deploy smoke; Vercel + Render deploy via Git |

Path filters skip unchanged areas on PRs (Python vs Studio). Push to `main` always runs all jobs.

**Deploy (PaaS Option 3):** Vercel (`apps/studio`) + Render (API via `Dockerfile` + `render.yaml`) + Neon (Postgres). LLM: Gemini or OpenRouter — not Ollama on free PaaS.

See **[infra/deploy/paas.md](infra/deploy/paas.md)** for first-time setup and env vars (`.env.production.example`).

```bash
# Local parity with CI
uv sync
uv run ruff check apps packages
uv run ruff format --check apps packages
uv run pytest
cd apps/studio && npm ci && npm test && npm run build
```

## License

Private — all rights reserved.
