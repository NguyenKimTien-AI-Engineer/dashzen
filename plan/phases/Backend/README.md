# DashZen Backend — Phased Implementation

> Chia từ [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) (§18 authoritative, §3 subsystem catalog).
>
> **Nguồn sự thật gốc** vẫn là file planner — các phase file này là bản triển khai có thứ tự theo **11 subsystem** Agent Runtime.

---

## Tổng quan

| Phase | Tên | Mục tiêu | Map §18 | Ưu tiên |
|-------|-----|----------|---------|---------|
| [Auth](./auth/) | **Auth Slice** | JWT login, route guard, task ownership | Slice 1 | P0 |
| [Phase 1](./phase-1-foundation.md) | Foundation & Minimal Loop | Infra, DB, LLM, chat stream, 1 agent → mock spec | P0 + P1 | P0–P1 |
| [Phase 2](./phase-2-agent-pipeline.md) | Full Pipeline & Production | 5 sub-agents, workflow, gates, compaction, artifacts | P2 + P3 | P1–P2 |
| [Phase 3](./phase-3-scale-production.md) | RAG, Data & Observability | Catalog RAG, CSV, eval CI, tracing, connectors | P5 + ⑪ | P2–P3 |

> **Lưu ý:** §18 **P4** (Studio UI đầy đủ) thuộc [`plan/phases/UI/UX/`](../UI/UX/) — không nằm trong Backend phases.

---

## 11 Subsystem → Phase mapping

| # | Subsystem | Phase 1 | Phase 2 | Phase 3 |
|---|-----------|---------|---------|---------|
| ① | Orchestration | main_loop minimal, agent_loop basic | spawn, workflow, recovery, title | polish, parallel exec |
| ② | Agent Registry | loader + `dashboard-planner` | 5 agents + workflows | hot reload, cache |
| ③ | Memory | seed `memory.md` | FSM, context block, workflows | user prefs block |
| ④ | Tool | file tools basic | full pipeline, tiers, loop detect | RAG catalog, data tools |
| ⑤ | Context | budget constants | 2-tier compaction, accounting | calibrated tokens |
| ⑥ | LLM | Ollama + 1 cloud adapter | streaming full, recovery signals | model routing |
| ⑦ | Gate | — (Auto mode only) | tool + ask gates, CAS, feedback | sub-agent gate routing |
| ⑧ | Artifact | basic file write | ArtifactBuffer, flush, upload | branch-scoped artifacts |
| ⑨ | Streaming | SSE core, lock basic | full guards, rate limit, stop | dedup, safety-net polish |
| ⑩ | Persistence | models, message tree flat | branching, AgentRun activities | export schemas |
| ⑪ | Observability | structlog basic | correlation ID | OpenTelemetry, eval CI |

---

## Phụ thuộc giữa các phase

```
Phase 1 (P0 + P1)
    │
    ├── Docker: postgres, redis, minio
    ├── packages/core (LLM ⑥) + packages/db (⑩)
    ├── apps/api: auth, tasks CRUD, stream SSE
    ├── Orchestration ① minimal + Streaming ⑨ core
    └── dashboard-planner ② → mock spec.md
            │
            ▼
Phase 2 (P2 + P3)
    │
    ├── Memory FSM ③ + 5-agent workflow ①②
    ├── Tool pipeline ④ + Context compaction ⑤
    ├── Gate HITL ⑦ + Artifact buffer ⑧
    └── Stream guards + rate limits ⑨
            │
            ▼
Phase 3 (P5 + ⑪)
    │
    ├── RAG catalog (Qdrant) + search_components
    ├── CSV upload + data tools
    ├── Eval golden sets + CI gate
    └── OpenTelemetry + SQL connectors (optional)
```

---

## Mapping section planner → phase

| Section | Phase |
|---------|-------|
| §1–§2 Vision & Tech Stack | 1 (foundation) |
| §3 System-of-systems catalog | All (reference) |
| §4 Orchestration | 1 → 2 |
| §5 Agent Registry | 1 (1 agent) → 2 (full) |
| §6 Memory | 1 (seed) → 2 (FSM) |
| §7 Tool System | 1 (basic) → 2 (pipeline) → 3 (RAG) |
| §8 Context System | 1 (budget) → 2 (compaction) |
| §9 LLM System | 1 |
| §10 Gate System | 2 |
| §11 Artifact System | 1 (basic) → 2 (buffer) |
| §12 Streaming System | 1 (core) → 2 (guards, rate limit) |
| §13 Persistence | 1 (models) → 2 (branching) |
| §14 Observability | 1 (structlog) → 3 (OTel, eval) |
| §15 Folder structure | 1 (scaffold) |
| §16 API surface | 1 (subset) → 2 (full) |
| §17 Decisions (MVP) | 1–2 |
| §18 Phased rollout | **Authoritative split** |
| §19–§21 Self-built, gaps, next steps | Cross-phase |

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) | SSE schema, FE integration (P4) |
| [`03-agent-runtime-and-memory.md`](../../03-agent-runtime-and-memory.md) | Orchestration detail, gates FSM |
| [`04-dashboard-spec-schema.md`](../../04-dashboard-spec-schema.md) | DashboardSpec Pydantic |
| [`06-api-contracts.md`](../../06-api-contracts.md) | OpenAPI, branching, rate limits |
| [`plan/phases/UI/UX/`](../UI/UX/) | Frontend phases (P4) |
