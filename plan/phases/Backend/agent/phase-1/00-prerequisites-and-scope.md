# 00 — Prerequisites & Scope (Phase 1)

> Đọc file này **trước** khi implement bất kỳ subsystem nào trong Phase 1.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §2, §3, §4 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md)

---

## 1. Vision Phase 1

Phase 1 là **nền móng Agent Runtime** — chứng minh luồng cốt lõi hoạt động:

```
User prompt
  → POST /v1/tasks/{id}/stream
  → main_loop (orchestrator)
  → spawn_agent("dashboard-planner")
  → agent_loop (isolated)
  → write_file("spec.md")
  → file_artifact SSE
  → stream_done
```

Không cần dashboard hoàn chỉnh (`page.tsx`), không cần workflow deterministic, không cần RAG. Chỉ cần **một turn chat → một agent → một file output**.

---

## 2. Subsystem trong scope Phase 1

| # | Subsystem | Mức độ Phase 1 | File plan |
|---|-----------|----------------|-----------|
| ⑥ | LLM | Ollama (dev) + 1 cloud adapter | [02-llm-system.md](./02-llm-system.md) |
| ⑩ | Persistence | Models + CRUD, message tree flat | [03-persistence-system.md](./03-persistence-system.md) |
| ① | Orchestration | `run_task()`, main_loop, agent_loop, spawn basic | [05-orchestration-system.md](./05-orchestration-system.md) |
| ⑨ | Streaming | EventBus, SSE schema core, stream lock | [04-streaming-system.md](./04-streaming-system.md) |
| ② | Agent Registry | Loader + `dashboard-planner` only | [06-agent-registry.md](./06-agent-registry.md) |
| ④ | Tool | File tools + registry tiers stub | [07-tool-system.md](./07-tool-system.md) |
| ⑧ | Artifact | Write stage → flush (basic) | [08-artifact-system.md](./08-artifact-system.md) |
| ⑤ | Context | Chỉ export budget constants | [02-llm-system.md](./02-llm-system.md) §5 |
| ③ | Memory | Chưa FSM — seed `memory.md` khi tạo task | [03-persistence-system.md](./03-persistence-system.md) |
| ⑦ | Gate | **Không** — Auto mode only | — |
| ⑪ | Observability | structlog basic | [01-infra-and-monorepo.md](./01-infra-and-monorepo.md) |

---

## 3. Nguyên tắc kiến trúc (áp dụng ngay Phase 1)

Các nguyên tắc sau lấy từ master plan §2.3 — **không đợi Phase 2** mới tuân thủ:

| # | Nguyên tắc | Áp dụng Phase 1 |
|---|------------|-----------------|
| 1 | Không dùng LangGraph/LangChain/CrewAI | Self-built runtime |
| 2 | Dual-loop tách biệt | `main_loop.py` vs `agent_loop.py` |
| 3 | Artifact buffer | Stage writes, flush on `stream_done` |
| 4 | Platform-agnostic core | API route chỉ gọi `run_task()`, không import `main_loop` trực tiếp |
| 5 | Observable execution | Mọi tool call emit SSE event |
| 6 | Interruptible | Abort signal propagate; client disconnect không cancel LLM |

**Chưa áp dụng Phase 1:** initGate, compaction, withGate (ask mode), recovery paths đầy đủ.

---

## 4. Constants production-proven

Tất cả constants tập trung tại `packages/agents/src/agents/orchestration/constants.py`. **Không hardcode rải rác.**

### 4.1 Vòng lặp chính

| Constant | Giá trị | Dùng ở Phase 1 |
|----------|---------|----------------|
| `MAX_ITERATIONS` | 40 | main_loop iteration cap |
| `MAX_AGENTS_PER_TURN` | 3 | spawn_agent overflow cap |
| `RECOVERY_LIMIT` | 5 | Defer recovery đầy đủ — stub counter |
| `TITLE_FORCE_BY_TURN` | 8 | Auto-title từ turn 8 |

### 4.2 Sub-agent

| Constant | Giá trị | Dùng ở Phase 1 |
|----------|---------|----------------|
| `SUBAGENT_MAX_TURNS` | 40 | agent_loop cap |
| `SUBAGENT_TIMEOUT_MS` | 1,080,000 (18 phút) | agent_loop wall-clock timeout |
| `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT` | 3 | agent recovery stub |

### 4.3 Context & budget (export FE)

| Constant | Giá trị |
|----------|---------|
| `LLM_CONTEXT_WINDOW` | 128,000 |
| `MICRO_COMPACT_FRACTION` | 0.60 |
| `SUMMARY_COMPACT_FRACTION` | 0.80 |
| `KEEP_TOKENS` | 40,000 |
| `INITIAL_TOKENS_PER_CHAR` | 0.34 |
| `IMAGE_CHAR_EQUIV` | 6,000 |

### 4.4 Tool execution

| Constant | Giá trị |
|----------|---------|
| `MAX_CONCURRENT_TOOLS` | 5 |

### 4.5 Stream lock

| Constant | Giá trị |
|----------|---------|
| `LOCK_TTL_SEC` | 90 |
| `LOCK_REFRESH_INTERVAL_MS` | 20,000 |

### 4.6 Artifact & spawn output

| Constant | Giá trị |
|----------|---------|
| `ACTIVITY_RESULT_MAX` | 2,000 |
| `ACTIVITY_COUNT_MAX` | 200 |
| `AGENT_OUTPUT_COMPACT_THRESHOLD` | 4,000 |
| `SPAWN_SUMMARY_MAX` | 2,000 |

---

## 5. Data flow tổng thể Phase 1

```
POST /v1/tasks/{id}/stream
  │
  ├─ acquire_stream_lock(task_id) → 409 nếu locked
  ├─ ArtifactBuffer() shared
  ├─ run_task(RuntimeContext)
  │    └─ main_loop() [async generator]
  │         ├─ persist user message
  │         ├─ load history + memory.md
  │         ├─ title generation (concurrent)
  │         ├─ for iteration in 0..MAX_ITERATIONS:
  │         │    ├─ LLM stream → yield main_text
  │         │    ├─ tool calls → exec_parallel
  │         │    │    └─ spawn_agent → agent_loop → agent_* events
  │         │    │         └─ write_file → ArtifactBuffer.stage + file_artifact
  │         │    └─ persist assistant + tool messages
  │         ├─ flush ArtifactBuffer
  │         └─ yield stream_done
  │
  └─ finally: release_stream_lock, cancel heartbeat
```

---

## 6. Prerequisites checklist

Trước khi code Phase 1, xác nhận:

- [ ] 1. Auth backend Done — `POST /v1/auth/login` trả JWT cookie
- [ ] 2. User model tồn tại trong DB (migration auth)
- [ ] 3. Đã đọc `01-project-structure-and-techstack.md` §3.2 (subsystem map)
- [ ] 4. Đã đọc `research/02-leadzen-agent-research.md` §3 (main-run flow)
- [ ] 5. Ollama cài local hoặc có Anthropic API key cho test
- [ ] 6. Docker + Docker Compose sẵn sàng trên máy dev

---

## 7. Quyết định MVP Phase 1

| Quyết định | Phase 1 |
|------------|---------|
| Auth | JWT httpOnly (đã có) |
| LLM dev | Ollama local |
| Mode | Auto only (không ask/gate) |
| Generated output | `spec.md` (mock DashboardSpec) |
| Data sources | Mock — không CSV/SQL |
| Streaming | SSE |
| Terminology | Task |
| Agent count | 1 (`dashboard-planner`) |

---

## 8. Cross-references

| File | Mục đích |
|------|----------|
| [01-infra-and-monorepo.md](./01-infra-and-monorepo.md) | Bước implement đầu tiên |
| [10-checklist.md](./10-checklist.md) | Definition of done cuối phase |
| [`auth/00-docker-postgres.md`](../auth/00-docker-postgres.md) | Postgres đã setup cho auth — mở rộng compose |
