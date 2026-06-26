# Track A — Phase 2: Full 5-Agent Dashboard Pipeline

> Plan triển khai chi tiết cho **Phase 2 Track A** — tách từ [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.
>
> **Mục tiêu:** Dashboard workflow đầy đủ end-to-end — từ yêu cầu ngôn ngữ tự nhiên đến `page.tsx` deployable. HITL gates (ask mode). Context compaction. Artifact buffer production-safe.
>
> **Deliverable cuối phase:** User nói *"tạo dashboard doanh thu theo khu vực"* → 5 agents chạy tuần tự → `spec.md`, `bindings.md`, `layout.md`, `page.tsx`, `review.md` → critic PASS → dashboard sẵn sàng preview.

---

## Trạng thái

| Thành phần | Trạng thái |
|------------|------------|
| ③ Memory System (FSM) | Planned |
| ② Agent Registry (5 agents + workflows) | Planned |
| ① Orchestration (workflow engine + recovery) | Planned |
| ④ Tool System (6-step pipeline) | Planned |
| ⑤ Context System (compaction) | Planned |
| ⑦ Gate System (HITL) | Planned |
| ⑧ Artifact (production buffer + upload) | Planned |
| ⑨ Streaming (full guards + rate limits) | Planned |
| ⑩ Persistence (branching + AgentRun reload) | Planned |
| API extensions (gates, upload, compact) | Planned |
| E2E Phase 2 | Planned |

---

## Tài liệu trong thư mục

| File | Nội dung |
|------|----------|
| [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) | Scope, phụ thuộc Phase 1, subsystem map Phase 2 |
| [01-memory-system.md](./01-memory-system.md) | ③ FSM, memory.md, context block, set_memory |
| [02-agent-registry-and-workflows.md](./02-agent-registry-and-workflows.md) | ② 5 agents + 4 workflow files |
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | ① workflow.py, recovery.py, exec_parallel full |
| [04-tool-system-full-pipeline.md](./04-tool-system-full-pipeline.md) | ④ pipeline 6 bước + tools mới |
| [05-context-system-compaction.md](./05-context-system-compaction.md) | ⑤ history, compaction, accounting, thinking codec |
| [06-gate-system-hitl.md](./06-gate-system-hitl.md) | ⑦ gate service, ask gate, cleanup |
| [07-artifact-and-upload.md](./07-artifact-and-upload.md) | ⑧ flush_and_remap + upload endpoint |
| [08-streaming-and-rate-limits.md](./08-streaming-and-rate-limits.md) | ⑨ production guards + rate limiting |
| [09-persistence-branching.md](./09-persistence-branching.md) | ⑩ message tree branching + AgentRun reload |
| [10-api-layer-extensions.md](./10-api-layer-extensions.md) | Gates, upload, compact, messages branch_info |
| [11-checklist.md](./11-checklist.md) | Definition of done 15 items + test cases |

---

## Scope Phase 2

### In scope

| Hạng mục | Chi tiết |
|----------|----------|
| Memory FSM | `set_memory`, workflow inject, Task.type sync |
| 5 agents | planner, binder, designer, builder, critic |
| 4 workflows | create/edit/repair-dashboard, create-chat |
| Workflow engine | Deterministic 5-agent spawn sequence |
| Ask mode | HITL gates — tool approve + ask_user |
| Compaction | 2-tier micro + summary, manual compact API |
| Tool pipeline | 6-step validate→loop→cache→gate→execute→truncate |
| Upload | CSV/JSON/image/PDF attach |
| Branching | Regenerate → new branch, branch_info |
| Rate limits | 5 Redis token buckets |

### Out of scope (Phase 3+)

| Hạng mục | Lý do defer |
|----------|-------------|
| OTEL tracing, eval CI | Phase 3 |
| Export zip | Phase 3 |
| Security hardening đầy đủ | Phase 3 |
| Real DB schema introspection | Phase 3 (`schema_inspector` mock Phase 2) |
| RAG / document upload | Track B (Phase 4+) |

---

## Phụ thuộc

```
Phase 1 Done (13/13 checklist) ──► BẮT BUỘC
       │
       ├── 01 Memory ──► 03 Orchestration workflow
       ├── 02 Registry + workflows ──► 03 Orchestration
       ├── 06 Gates ──► 04 Tool pipeline step 4
       ├── 05 Context ──► 03 main_loop compaction
       ├── 07 Artifact ──► phantom prevention + upload
       └── 09 Persistence ──► branching API
```

**Điều kiện bắt đầu:**

1. [Phase 1 checklist](../phase-1/10-checklist.md) — **tất cả 13 items PASS**
2. Đã đọc [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5
3. Đã đọc `research/02-leadzen-agent-research.md` — gate service, compaction, set-memory FSM

---

## Thứ tự implement đề xuất

| Bước | File plan | Ghi chú |
|------|-----------|---------|
| 0 | [00](./00-prerequisites-and-scope.md) | Verify Phase 1 gate |
| 1 | [01](./01-memory-system.md) | FSM + set_memory trước workflow |
| 2 | [02](./02-agent-registry-and-workflows.md) | 5 agents + 4 workflow prompts |
| 3 | [06](./06-gate-system-hitl.md) | Gates trước tool pipeline step 4 |
| 4 | [04](./04-tool-system-full-pipeline.md) | 6-step pipeline + new tools |
| 5 | [05](./05-context-system-compaction.md) | History + compaction wire main_loop |
| 6 | [03](./03-orchestration-full-pipeline.md) | workflow.py + recovery + spawn withGate |
| 7 | [07](./07-artifact-and-upload.md) | flush_and_remap + upload |
| 8 | [08](./08-streaming-and-rate-limits.md) | Rate limits + production guards |
| 9 | [09](./09-persistence-branching.md) | branch_info + AgentRun in messages |
| 10 | [10](./10-api-layer-extensions.md) | Gates/upload/compact routes |
| 11 | [11](./11-checklist.md) | E2E verify 15 items |

---

## Cross-references

| File | Liên quan |
|------|-----------|
| [`00-master-agent-plan.md`](../00-master-agent-plan.md) | Nguồn gốc Phase 2 §5 |
| [`phase-1/`](../phase-1/) | Foundation — không rebuild từ đầu |
| [`research/02-leadzen-agent-research.md`](../../../research/02-leadzen-agent-research.md) | Gate, compaction, FSM reference |
| [`UI/02-ui-features-chat-agent.md`](../../UI/02-ui-features-chat-agent.md) | FE gates, branching, upload UI |
