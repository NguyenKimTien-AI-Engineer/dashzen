# Phase 1 — Foundation & Minimal Loop

> **Mục tiêu:** Nền tảng infra + agent runtime tối thiểu — chat stream hoạt động, `dashboard-planner` sinh mock spec.
>
> **Nguồn:** [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) §18 P0 + P1, §2, §9, §12 (subset), §13, §15, §16, §17
>
> **Ưu tiên:** P0–P1 | **Map §18:** P0 + P1

---

## 1. Vision & scope

Phase 1 dựng **Agent Runtime host** với wiring tối thiểu — đủ để Studio UI (Phase 1 FE) gọi API và nhận SSE stream.

```
User prompt → POST /stream → main_loop → dashboard-planner → spec.md → file_artifact SSE
```

### Subsystem trong scope

| # | Subsystem | Mức độ Phase 1 |
|---|-----------|----------------|
| ⑥ | LLM | Ollama (dev) + 1 cloud adapter |
| ⑩ | Persistence | Models + CRUD, message tree (flat, chưa branch) |
| ① | Orchestration | `run_task()`, main_loop minimal, agent_loop basic |
| ⑨ | Streaming | EventBus, SSE schema core, stream lock cơ bản |
| ② | Agent Registry | Loader + `dashboard-planner` only |
| ④ | Tool | File tools: `read_file`, `write_file`, `list_file` |
| ⑧ | Artifact | Write trực tiếp (chưa buffer đầy đủ) |
| ⑤ | Context | Budget constants export (`GET /v1/llm/budget`) |

### Không thuộc Phase 1

- Memory FSM transitions đầy đủ, workflow plugins
- 4 sub-agent còn lại (data-binder, layout-designer, builder, critic)
- Gate System (HITL) — chạy **Auto mode** only
- 2-tier compaction, manual compact API
- Tool pipeline đầy đủ (loop detection, gate, batching)
- Message tree branching
- Rate limiting matrix
- RAG / Qdrant
- OpenTelemetry, eval golden sets

---

## 2. Tech foundation

### 2.1 Stack

| Layer | Công nghệ |
|-------|-----------|
| Language | Python 3.12+ |
| API | FastAPI + Pydantic v2 |
| Package manager | uv |
| App DB | PostgreSQL |
| Cache / lock | Redis |
| Object storage | MinIO (S3-compatible) |
| LLM dev | Ollama |
| Logging | structlog (basic) |

### 2.2 Infra (Docker Compose)

- [ ] `postgres` — app database
- [ ] `redis` — stream lock, (gates placeholder)
- [ ] `minio` — workspace files, uploads
- [ ] `.env.example` — connection strings, JWT secret, LLM keys
- [ ] Health checks cho tất cả services

### 2.3 Monorepo scaffold (§15)

```
dashzen/
├── apps/api/           # FastAPI adapter
├── packages/
│   ├── core/           # config, llm, schemas, exceptions
│   ├── agents/         # runtime subsystems
│   ├── tools/          # file handlers (phase 1)
│   └── db/             # SQLAlchemy models
└── infra/compose/
```

**Dependency direction:** `api → agents, db, core` | `agents → tools, db, core` | `tools → core`

---

## 3. Deliverables checklist

### 3.1 ⑥ LLM System (§9)

- [ ] `LLMClient` Protocol — `chat()`, `stream()`
- [ ] `providers/ollama.py` — dev default
- [ ] `providers/anthropic.py` hoặc `openai.py` — 1 cloud adapter
- [ ] `LLMDelta` — text / thinking / tool_call
- [ ] Failure signals: `max_tokens`, `empty`, `thinking_only` → báo Orchestration
- [ ] `core/llm/budget.py` — shared constants:

```python
LLM_CONTEXT_WINDOW = 128_000
LLM_INPUT_BUDGET_TOKENS = ...
COMPACT_THRESHOLD_PCT = 50
```

- [ ] Export budget → `GET /v1/llm/budget` (FE donut Phase 2)

### 3.2 ⑩ Persistence System (§13)

**Models:**

| Model | Fields chính |
|-------|--------------|
| `Task` | title, user_id, status, `type` |
| `Message` | role (user/assistant/tool), content, `parent_id` (nullable, chưa branch) |
| `File` | source, kind, path, task_id |
| `AgentRun` | activities JSON, status, agent_name |

- [ ] Alembic migrations
- [ ] `POST /v1/tasks` — tạo task + seed `memory.md` (`type: chat`)
- [ ] `GET /v1/tasks` — list recents
- [ ] `GET/PATCH/DELETE /v1/tasks/{id}`
- [ ] `GET /v1/tasks/{id}/messages` — flat list (branching → Phase 2)
- [ ] `GET /v1/tasks/{id}/artifacts` — workspace files

**Schemas cốt lõi (`core/schemas/`):**

- [ ] `StreamEvent` union type
- [ ] `AgentActivity` timeline entry
- [ ] `DashboardSpec` — stub/minimal (full → plan 04)

### 3.3 ⑨ Streaming System — core (§12)

**SSE events (Phase 1 subset):**

| Event | Phase 1 |
|-------|---------|
| `main_text`, `main_tool`, `main_result` | ✓ |
| `agent_start`, `agent_tool`, `agent_result`, `agent_done` | ✓ |
| `file_artifact`, `task_meta` | ✓ |
| `stream_done`, `stream_error`, `heartbeat` | ✓ |
| `main_think`, `main_ask` | defer Phase 2 |

- [ ] `event_bus.py` — internal → SSE serializer
- [ ] `events.py` — Pydantic event types
- [ ] `lock.py` — `acquire_stream_lock` → 409 nếu đang chạy
- [ ] Heartbeat 5s refresh Redis TTL
- [ ] Client disconnect → **không abort** LLM
- [ ] `POST /v1/tasks/{id}/stream` — main chat stream
- [ ] `POST /v1/tasks/{id}/stop` — abort cơ bản

### 3.4 ① Orchestration — minimal (§4)

- [ ] `runtime.py` — `run_task()`, wiring `RuntimeContext`
- [ ] `main_loop.py` — orchestrator loop, max 40 iterations
- [ ] `agent_loop.py` — sub-agent loop ephemeral
- [ ] `spawn.py` — basic spawn, parse Status/Summary contract
- [ ] Dual-loop: main persist messages, sub-agent → `AgentRun.activities` only
- [ ] Iteration guard: max 40/turn, max 3 spawn/turn (enforce nhưng 1 agent thôi)
- [ ] Title generation cơ bản — turns 1–7, emit `task_meta` SSE

**Chưa có Phase 1:**

- `workflow.py` deterministic pipeline
- `recovery.py` đầy đủ
- `exec_parallel.py`

### 3.5 ② Agent Registry (§5)

- [ ] `loader.py` — `load_agent_registry()`, `load_system_prompt()`
- [ ] `cache.py` — parse cache
- [ ] `schema.py` — Pydantic frontmatter model
- [ ] Load `prompts/system/system-main.md`, `system-agent.md`
- [ ] Load `prompts/agents/dashboard-planner.md` only
- [ ] Validate frontmatter: name, tools, maxTurns

### 3.6 ④ Tool System — basic (§7)

- [ ] `packages/tools/file/` — `read_file`, `write_file`, `list_file`
- [ ] Tool contract `ToolHandler` Protocol
- [ ] Registry: `READ_ONLY_TOOLS`, `MAIN_TOOLS`, `AGENT_TOOLS` constants (stub tiers)
- [ ] Execute trực tiếp — **chưa** full pipeline (validate→loop→gate→truncate)

### 3.7 ⑧ Artifact — basic (§11)

- [ ] `write_file` → lưu workspace (`spec.md`, `memory.md`)
- [ ] Emit `file_artifact` SSE khi file thay đổi
- [ ] `File` model CRUD qua `file_service.py` basic
- [ ] Storage path: `attachments/{task_id}/`

### 3.8 apps/api — REST + SSE (§16)

| Endpoint | Phase 1 |
|----------|---------|
| `POST /v1/auth/login` | ✓ JWT httpOnly |
| `POST /v1/auth/refresh` | ✓ |
| `POST/GET/PATCH/DELETE /v1/tasks` | ✓ |
| `GET /v1/tasks/{id}/messages` | ✓ |
| `GET /v1/tasks/{id}/artifacts` | ✓ |
| `POST /v1/tasks/{id}/stream` | ✓ |
| `POST /v1/tasks/{id}/stop` | ✓ |
| `GET /v1/llm/budget` | ✓ |
| Gates, compact, upload | Phase 2 |

- [ ] `deps.py` — DB session, current user
- [ ] JWT middleware — single-user MVP (§17)
- [ ] `fetchWithAuth` pattern align FE plan 02

### 3.9 Quyết định MVP (§17)

| Quyết định | Phase 1 |
|------------|---------|
| Auth | Single-user + JWT |
| LLM dev | Ollama local |
| Generated page | Runtime JSON spec (mock) |
| Data sources | Mock data only |
| Streaming | SSE |
| Terminology | Task |

---

## 4. Definition of done

Phase 1 hoàn thành khi:

1. `docker compose up` → postgres, redis, minio healthy
2. User login → JWT cookie → tạo task
3. Gửi prompt qua `POST /stream` → nhận SSE `main_text` + `agent_*` events
4. `dashboard-planner` spawn → ghi `spec.md` → `file_artifact` SSE
5. `GET /messages` + `GET /artifacts` restore state sau refresh
6. `POST /stop` abort stream đang chạy
7. 409 khi stream task đang processing
8. Studio UI Phase 1 có thể integrate end-to-end

---

## 5. Gaps Phase 1 (từ §20)

| Gap | Action |
|-----|--------|
| `main_loop` iteration detail | Implement minimal, chi tiết → plan 03 |
| SSE schema | Core events; full → plan 06 |
| `DashboardSpec` full | Stub; full → plan 04 |
| MVP scope chốt | Coordinate plan 05 |

---

## 6. Tiếp theo

Xem [`phase-2-agent-pipeline.md`](./phase-2-agent-pipeline.md) — full 5-agent pipeline, gates, compaction.
