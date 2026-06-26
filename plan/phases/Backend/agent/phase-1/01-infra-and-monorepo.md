# 01 — Infra & Monorepo Scaffold

> Dựng hạ tầng Docker + cấu trúc monorepo `uv` workspaces + Alembic migrations.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.1 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §4, §5

**Phụ thuộc:** [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) | Auth Postgres đã có ([`auth/00-docker-postgres.md`](../auth/00-docker-postgres.md))

---

## 1. Mục tiêu

- [ ] 1. `docker compose up` → postgres + redis + minio healthy trong 30 giây
- [ ] 2. Monorepo 5 packages scaffold với dependency direction đúng
- [ ] 3. Alembic migration 001 tạo 4 tables Phase 1
- [ ] 4. `.env.example` đầy đủ, không hardcode credential trong code

---

## 2. Docker Compose services

**File:** `infra/compose/docker-compose.yml` — mở rộng service Postgres đã có từ Auth.

### 2.1 PostgreSQL 16

| Setting | Giá trị |
|---------|---------|
| Image | `postgres:16-alpine` |
| Healthcheck | `pg_isready -U dashzen -d dashzen` |
| Volume | `dashzen_pg_data` — persistent |

Postgres đã tồn tại từ Auth — **không tạo duplicate**. Chỉ verify healthcheck và volume.

### 2.2 Redis 7 Alpine

| Setting | Giá trị |
|---------|---------|
| Image | `redis:7-alpine` |
| Command | `redis-server --appendonly yes` |
| Port | `6379:6379` |
| Volume | `dashzen_redis_data` |
| Healthcheck | `redis-cli ping` |

**Vai trò Phase 1:** Stream lock (`SET NX EX`), heartbeat refresh. Gate keys defer Phase 2.

### 2.3 MinIO (S3-compatible)

| Setting | Giá trị |
|---------|---------|
| Image | `minio/minio` |
| Ports | `9000` (API), `9001` (console) |
| Volume | `dashzen_minio_data` |
| Healthcheck | HTTP `/minio/health/live` |

**Vai trò Phase 1:** Object storage cho binary/image files. Text workspace files lưu DB column `content` — MinIO sẵn sàng cho Phase 2 upload.

### 2.4 Checklist Docker

- [ ] 1. Thêm `redis` và `minio` services vào compose (giữ `postgres` hiện có)
- [ ] 2. Mỗi service có persistent volume
- [ ] 3. Mỗi service có healthcheck
- [ ] 4. `depends_on` với `condition: service_healthy` nếu API chạy trong compose (optional dev)
- [ ] 5. `docker compose -f infra/compose/docker-compose.yml up -d` → cả 3 healthy
- [ ] 6. Không crash sau 30 giây idle

---

## 3. Environment variables

**File:** `.env.example` — nhóm biến theo service.

### 3.1 Database

```env
DATABASE_URL=postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen
```

### 3.2 Redis

```env
REDIS_URL=redis://localhost:6379/0
```

### 3.3 MinIO

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=dashzen
MINIO_SECRET_KEY=dashzen-secret
MINIO_BUCKET=dashzen-workspace
MINIO_USE_SSL=false
```

### 3.4 JWT (từ Auth — không duplicate logic)

```env
JWT_SECRET=<random-64-bytes>
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7
```

### 3.5 LLM providers

```env
LLM_PROVIDER=ollama          # ollama | anthropic | openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o
```

### 3.6 App

```env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=info
```

### 3.7 Checklist env

- [ ] 1. `.env.example` commit vào repo
- [ ] 2. `.env` trong `.gitignore`
- [ ] 3. Không hardcode credential trong Python/TS source
- [ ] 4. `packages/core` đọc config qua `pydantic-settings` hoặc tương đương

---

## 4. Monorepo packages scaffold

**Tool:** `uv` workspaces (theo `01-project-structure-and-techstack.md` §4).

### 4.1 Package layout

```
apps/
  api/                    # FastAPI adapter — routes only
packages/
  core/                   # LLM client, schemas, config — ZERO agent logic
  agents/                 # Agent runtime subsystems
  tools/                  # Tool implementations/handlers
  db/                     # SQLAlchemy models + Alembic
```

### 4.2 Dependency direction (bắt buộc)

```
api  →  agents, db, core
agents  →  tools, db, core
tools  →  core
db  →  (standalone, không import agents)
core  →  (standalone, KHÔNG import agents)
```

### 4.3 Checklist scaffold

- [ ] 1. Root `pyproject.toml` với `[tool.uv.workspace]` members
- [ ] 2. Mỗi package có `pyproject.toml` + `src/` layout
- [ ] 3. `apps/api` có FastAPI app factory `create_app()`
- [ ] 4. `packages/core/src/core/` — config, llm stub
- [ ] 5. `packages/agents/src/agents/` — subsystem folders empty/stub
- [ ] 6. `packages/tools/src/tools/` — file/ stub
- [ ] 7. `packages/db/src/db/` — base, session factory
- [ ] 8. Verify import direction: `core` không import `agents`

### 4.4 Dev commands

- [ ] 1. `uv sync` install toàn workspace
- [ ] 2. `uv run uvicorn api.main:app --reload` start API
- [ ] 3. `uv run alembic upgrade head` migrate DB

---

## 5. Alembic migration setup

**Location:** `packages/db/`

### 5.1 Configuration

- [ ] 1. `alembic.ini` đọc `DATABASE_URL` từ environment — không hardcode
- [ ] 2. `env.py` dùng async SQLAlchemy engine
- [ ] 3. `target_metadata` trỏ tới `Base.metadata` từ models

### 5.2 Migration 001 — initial schema

Migration đầu tiên tạo **4 tables Phase 1** (+ `users` từ Auth nếu chưa có):

| Table | Mô tả |
|-------|-------|
| `users` | Auth (đã có từ auth migration) |
| `tasks` | Conversation container |
| `messages` | Message tree |
| `files` | Workspace + upload files |
| `agent_runs` | Sub-agent activity timeline |

Chi tiết columns: xem [03-persistence-system.md](./03-persistence-system.md).

### 5.3 Checklist migration

- [ ] 1. `alembic revision --autogenerate -m "001_initial_agent_schema"`
- [ ] 2. Review migration SQL — không drop auth tables
- [ ] 3. `alembic upgrade head` trên fresh DB thành công
- [ ] 4. `alembic downgrade -1` + `upgrade head` round-trip OK

---

## 6. Structlog basic (Phase 1)

- [ ] 1. Config structlog JSON renderer cho production path
- [ ] 2. Human-readable renderer cho local dev
- [ ] 3. Bind `task_id` khi xử lý stream request (correlation)

Observability đầy đủ (OTEL, eval) → Phase 3.

---

## 7. Definition of done — step 01

- [ ] `docker compose up` → postgres, redis, minio healthy
- [ ] `.env.example` đầy đủ nhóm biến
- [ ] 5 packages scaffold, `uv sync` OK
- [ ] Alembic migration 001 apply thành công
- [ ] API `GET /health` trả 200 (stub route)

---

## 8. Cross-references

| File | Tiếp theo |
|------|-----------|
| [02-llm-system.md](./02-llm-system.md) | LLM client sau infra |
| [03-persistence-system.md](./03-persistence-system.md) | Model details cho migration |
| [`auth/00-docker-postgres.md`](../auth/00-docker-postgres.md) | Postgres baseline |
