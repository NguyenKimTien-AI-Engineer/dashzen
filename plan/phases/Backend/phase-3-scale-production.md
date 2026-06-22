# Phase 3 — RAG, Data & Observability

> **Mục tiêu:** Component catalog RAG, data connectors, eval CI gate, distributed tracing — sẵn sàng scale production.
>
> **Nguồn:** [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) §18 P5, §7.6, §14, §17, §19–§20
>
> **Ưu tiên:** P2–P3 | **Map §18:** P5 + ⑪ | **Phụ thuộc:** Phase 1 + Phase 2 hoàn thành

---

## 1. Scope overview

Phase 3 mở rộng **data plane** và **observability** — không block MVP hay full pipeline:

- **RAG catalog** — `search_components` cho planner/builder grounded
- **Data sources** — CSV upload, schema inspect (SQL connector optional)
- **Eval** — golden sets validate dashboard spec + render success
- **Observability** — OpenTelemetry traces, structured logs production
- **Export** — generated page file export (align §17 phase 2)

### Không thuộc Phase 3 (out of scope / later)

- LangGraph, LangChain, CrewAI, MCP — **không dùng** (§19)
- Multi-tenant auth full — interface sẵn, implement khi product cần
- `spawn_task` multi-task parallel

---

## 2. Deliverables checklist

### 2.1 ④ Tool System — RAG catalog (§7.6)

- [ ] `packages/rag/` — vector store integration
- [ ] Qdrant (hoặc pgvector) trong Docker Compose
- [ ] Index widget templates từ `templates/`
- [ ] `search_components` tool — semantic search catalog
- [ ] Embeddings pipeline — chunk + ingest + refresh
- [ ] Planner/builder dùng catalog — grounded component selection
- [ ] Eval: search relevance golden set

### 2.2 Data tools & connectors (§17)

**MVP data (Phase 2 basic) → Phase 3 full:**

| Tool | Mô tả |
|------|-------|
| `csv_preview` | Parse + schema inference từ upload |
| `schema_inspector` | Validate binding against source |
| SQL connector | Phase 3 optional — query live DB |

- [ ] CSV upload → `data-binder` map metrics → queries
- [ ] Mock data fallback khi không có source
- [ ] Data connector approval gate (ActionCard mô tả connector)
- [ ] Validate grounded generation — không bịa metric

### 2.3 Generated page export (§17)

| Quyết định | Phase 3 |
|------------|---------|
| Generated page MVP | Runtime JSON spec |
| Export | **File export** — `page.tsx` + widgets deployable |

- [ ] `dashboard-builder` output validate + lint
- [ ] Export API — zip workspace files
- [ ] Schema validation fail → không deploy (fail-closed)

### 2.4 ⑪ Observability System (§14)

**Logging:**

- [ ] structlog production config — JSON format
- [ ] Correlation ID per `task_id` / `agent_run_id`
- [ ] Log levels: stream lifecycle, tool calls, gate events, compaction

**Tracing:**

- [ ] OpenTelemetry SDK wiring
- [ ] Spans: `run_task`, main_loop iteration, sub-agent spawn, tool execute, gate wait
- [ ] Export: Jaeger/Tempo local, OTLP prod
- [ ] Trace ID trong error responses (support debug)

**Eval (`packages/eval/`):**

- [ ] Golden sets — dashboard spec validity
- [ ] Render success checks — widget schema compliance
- [ ] CI gate — GitHub Actions chạy eval trước merge
- [ ] Regression suite cho workflow create-dashboard
- [ ] Prompt regression — agent output contract compliance

### 2.5 Production hardening

**Streaming polish:**

- [ ] Dedup tuning — false positive reduction
- [ ] Safety-net orphan lock monitoring + alert
- [ ] Stream metrics: duration, tokens, tool count per task

**Context & LLM:**

- [ ] Provider-calibrated `tokens_per_char` per model
- [ ] Model routing — fast model cho classify/title, full model cho orchestrator
- [ ] Cost tracking per task (optional dashboard internal)

**Security:**

- [ ] Upload validation — MIME, size cap, path traversal
- [ ] Task ownership trên mọi artifact/upload endpoint
- [ ] Rate limit tuning production
- [ ] Secrets management — env rotation guide

**Auth evolution (optional):**

- [ ] better-auth migration path (plan 02 §10.11)
- [ ] Multi-tenant `user_id` isolation audit
- [ ] OAuth providers nếu product yêu cầu

### 2.6 Infra & DevOps

- [ ] Docker Compose prod profile
- [ ] GitHub Actions: lint, typecheck, unit test, eval gate
- [ ] Database backup strategy
- [ ] Redis persistence config cho gates/locks
- [ ] MinIO bucket lifecycle policies

---

## 3. Definition of done

Phase 3 hoàn thành khi (tùy product priority):

1. `search_components` trả relevant widgets từ catalog indexed
2. CSV upload → data-binder tạo bindings grounded
3. Eval CI fail khi spec invalid hoặc render broken
4. OpenTelemetry trace visible cho full create-dashboard workflow
5. Export zip chứa deployable `page.tsx` + assets
6. Production logging searchable by `task_id`
7. (Optional) SQL connector query live và bind widget

---

## 4. Ưu tiên triển khai trong Phase 3

| # | Feature | Impact | Effort |
|---|---------|--------|--------|
| 1 | Eval golden sets + CI | Cao | Trung bình |
| 2 | RAG `search_components` | Cao | Cao |
| 3 | CSV upload + data-binder full | Cao | Trung bình |
| 4 | structlog production + correlation | Trung bình | Thấp |
| 5 | Export generated files | Trung bình | Trung bình |
| 6 | OpenTelemetry wiring | Trung bình | Trung bình |
| 7 | SQL connector | Tùy product | Cao |
| 8 | Multi-tenant auth | Tùy product | Cao |

---

## 5. Alignment §18 → 3 Backend phases

| §18 | Backend phase |
|-----|---------------|
| P0 Nền tảng | Phase 1 |
| P1 Loop tối thiểu | Phase 1 |
| P2 Full pipeline | Phase 2 |
| P3 Production patterns | Phase 2 |
| P4 Studio UI | [`UI/UX phases`](../UI/UX/) |
| P5 RAG + eval | Phase 3 |

---

## 6. Gaps & cross-references

| Gap (§20) | Phase 3 action |
|-----------|----------------|
| Eval golden sets + CI | §2.4 |
| OpenTelemetry wiring | §2.4 |
| `DashboardSpec` full validation | plan 04 + eval |
| SQL connector | §2.2 optional |

| File | Liên quan |
|------|-----------|
| [`04-dashboard-spec-schema.md`](../../04-dashboard-spec-schema.md) | Schema validation eval |
| [`06-api-contracts.md`](../../06-api-contracts.md) | Export API, rate limits |
| [`plan/phases/UI/UX/`](../UI/UX/) | FE Phase 3 export/share UI |
