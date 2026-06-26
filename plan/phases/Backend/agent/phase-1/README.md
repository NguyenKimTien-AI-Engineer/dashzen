# Track A — Phase 1: Foundation & Minimal Loop

> Plan triển khai chi tiết cho **Phase 1 Track A** — tách từ [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.
>
> **Mục tiêu:** Dựng hạ tầng + agent runtime tối thiểu — chat stream hoạt động end-to-end, một sub-agent ghi `spec.md`.
>
> **Deliverable cuối phase:** User gửi *"tạo dashboard doanh thu"* → main agent spawn `dashboard-planner` → planner ghi `spec.md` → FE nhận `file_artifact` SSE.

---

## Trạng thái

| Thành phần | Trạng thái |
|------------|------------|
| Infra (Docker, monorepo) | Planned |
| ⑥ LLM System | Planned |
| ⑩ Persistence | Planned |
| ⑨ Streaming (core) | Planned |
| ① Orchestration (minimal) | Planned |
| ② Agent Registry (1 agent) | Planned |
| ④ Tool System (basic) | Planned |
| ⑧ Artifact (basic) | Planned |
| API layer (tasks + stream) | Planned |
| E2E Phase 1 | Planned |

---

## Tài liệu trong thư mục

| File | Nội dung |
|------|----------|
| [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) | Scope, phụ thuộc, constants, nguyên tắc Phase 1 |
| [01-infra-and-monorepo.md](./01-infra-and-monorepo.md) | Docker Compose, `.env`, uv workspaces, Alembic |
| [02-llm-system.md](./02-llm-system.md) | ⑥ LLMClient, Ollama/Anthropic/OpenAI, budget API |
| [03-persistence-system.md](./03-persistence-system.md) | ⑩ Task, Message, File, AgentRun + CRUD |
| [04-streaming-system.md](./04-streaming-system.md) | ⑨ SSE schema, stream lock, EventBus, guards cơ bản |
| [05-orchestration-system.md](./05-orchestration-system.md) | ① runtime, main_loop, agent_loop, spawn, title, exec_parallel |
| [06-agent-registry.md](./06-agent-registry.md) | ② loader, schema, cache — chỉ `dashboard-planner` |
| [07-tool-system.md](./07-tool-system.md) | ④ registry tiers, loop/read_cache/partition, file tools |
| [08-artifact-system.md](./08-artifact-system.md) | ⑧ ArtifactBuffer, file_service |
| [09-api-layer.md](./09-api-layer.md) | REST tasks, SSE stream/stop, auth integration |
| [10-checklist.md](./10-checklist.md) | Definition of done, thứ tự implement, test cases |

---

## Scope Phase 1

### In scope

| Hạng mục | Chi tiết |
|----------|----------|
| Infra | PostgreSQL + Redis + MinIO qua Docker Compose |
| Agent runtime | Dual-loop tối thiểu (main + sub-agent) |
| Streaming | SSE core events + stream lock |
| Agent | Chỉ `dashboard-planner` |
| Tools | `read_file`, `write_file`, `list_file` |
| Mode | **Auto only** — chưa HITL gates |
| Auth | Tích hợp JWT đã có ([`auth/`](../auth/)) |

### Out of scope (Phase 2+)

| Hạng mục | Lý do defer |
|----------|-------------|
| Memory FSM + `set_memory` workflow | Phase 2 |
| 4 agents còn lại + workflow files | Phase 2 |
| HITL gates (ask mode) | Phase 2 |
| 2-tier context compaction | Phase 2 |
| Full tool pipeline (validate→gate→truncate) | Phase 2 |
| Message tree branching | Phase 2 |
| Rate limiting matrix | Phase 2 |
| Upload endpoint | Phase 2 |
| RAG / Qdrant / document upload | Track B (Phase 4+) |

---

## Phụ thuộc

```
Auth (Done) ──► user_id, JWT, get_current_user
       │
       ▼
Phase 1 Infra (01) ──► Postgres + Redis + MinIO
       │
       ├── 02 LLM ──► 05 Orchestration
       ├── 03 Persistence ──► 05, 08, 09
       ├── 04 Streaming ──► 09 API stream
       ├── 06 Registry + 07 Tools ──► 05 spawn
       └── 08 Artifact ──► 07 write_file
```

**Điều kiện bắt đầu:**

1. Auth backend hoạt động ([`auth/07-implementation-status.md`](../auth/07-implementation-status.md))
2. Đã đọc [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §1–§4, §15–§16
3. Đã đọc [`00-master-agent-plan.md`](../00-master-agent-plan.md) §2–§3

---

## Thứ tự implement đề xuất

| Bước | File plan | Ghi chú |
|------|-----------|---------|
| 0 | [00](./00-prerequisites-and-scope.md) | Đọc scope + constants |
| 1 | [01](./01-infra-and-monorepo.md) | `docker compose up` healthy |
| 2 | [02](./02-llm-system.md) | Ollama dev trước; Anthropic optional |
| 3 | [03](./03-persistence-system.md) | Migration 001 + models |
| 4 | [04](./04-streaming-system.md) | Events schema trước khi wire API |
| 5 | [08](./08-artifact-system.md) | Buffer trước write_file |
| 6 | [07](./07-tool-system.md) | File tools + registry tiers |
| 7 | [06](./06-agent-registry.md) | Prompts + loader |
| 8 | [05](./05-orchestration-system.md) | Main loop — phần lớn nhất |
| 9 | [09](./09-api-layer.md) | Wire HTTP/SSE |
| 10 | [10](./10-checklist.md) | E2E verify toàn bộ 13 items |

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`00-master-agent-plan.md`](../00-master-agent-plan.md) | Nguồn gốc Phase 1 §4 |
| [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) | Kiến trúc 11 subsystem, API surface |
| [`research/02-leadzen-agent-research.md`](../../../research/02-leadzen-agent-research.md) | Reference code TypeScript |
| [`auth/`](../auth/) | JWT, User model, login |
| [`UI/02-ui-features-chat-agent.md`](../../UI/02-ui-features-chat-agent.md) | FE SSE integration (Phase 1 FE) |
| [`UI/phase-1/`](../../UI/phase-1/) | **Plan triển khai UI Phase 1** — steps 00–10 |
