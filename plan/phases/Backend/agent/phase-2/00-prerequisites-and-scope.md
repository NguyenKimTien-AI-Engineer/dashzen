# 00 — Prerequisites & Scope (Phase 2)

> Đọc file này **trước** khi implement Phase 2. **Phase 1 phải Done hoàn toàn.**
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5 | [`phase-1/10-checklist.md`](../phase-1/10-checklist.md)

---

## 1. Vision Phase 2

Phase 2 mở rộng Phase 1 thành **full dashboard creation pipeline**:

```
User: "tạo dashboard doanh thu theo khu vực"
  → set_memory({ type: dashboard, phase: create-dashboard })
  → workflow engine take over
  → spawn dashboard-planner    → spec.md
  → spawn data-binder          → bindings.md
  → spawn layout-designer      → layout.md
  → spawn dashboard-builder    → page.tsx
  → spawn dashboard-critic     → review.md
  → critic PASS → dashboard preview ready
  → critic FAIL → repair-dashboard workflow
```

---

## 2. Subsystem trong scope Phase 2

| # | Subsystem | Mức độ Phase 2 | File plan |
|---|-----------|----------------|-----------|
| ③ | Memory | FSM + memory.md + context block + set_memory | [01-memory-system.md](./01-memory-system.md) |
| ② | Agent Registry | 5 agents + 4 workflow files | [02-agent-registry-and-workflows.md](./02-agent-registry-and-workflows.md) |
| ① | Orchestration | workflow.py, recovery.py, exec_parallel full, withGate | [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) |
| ④ | Tool | 6-step pipeline + edit_file, ask_user, schema_inspector, csv_preview | [04-tool-system-full-pipeline.md](./04-tool-system-full-pipeline.md) |
| ⑤ | Context | history, 2-tier compaction, accounting, thinking codec | [05-context-system-compaction.md](./05-context-system-compaction.md) |
| ⑦ | Gate | Full HITL — tool gate + ask gate | [06-gate-system-hitl.md](./06-gate-system-hitl.md) |
| ⑧ | Artifact | flush_and_remap + upload endpoint | [07-artifact-and-upload.md](./07-artifact-and-upload.md) |
| ⑨ | Streaming | Production guards + rate limiting | [08-streaming-and-rate-limits.md](./08-streaming-and-rate-limits.md) |
| ⑩ | Persistence | Message tree branching + AgentRun reload | [09-persistence-branching.md](./09-persistence-branching.md) |

**Giữ nguyên từ Phase 1 (extend, không rewrite):** LLM System, constants, stream lock core, EventBus schema.

---

## 3. Phase 1 gate — bắt buộc PASS

Không bắt đầu Phase 2 until [phase-1/10-checklist.md](../phase-1/10-checklist.md) — **13/13 items**:

- [ ] Docker healthy (postgres, redis, minio)
- [ ] Auth JWT
- [ ] Task CRUD + memory.md seed
- [ ] SSE stream + main_text
- [ ] spawn_agent dashboard-planner
- [ ] write_file spec.md + file_artifact
- [ ] Messages + artifacts restore
- [ ] Stop handshake
- [ ] 409 concurrent stream
- [ ] Disconnect không cancel LLM
- [ ] GET /llm/budget
- [ ] Auto-title

---

## 4. Nguyên tắc bổ sung Phase 2

| # | Nguyên tắc | Nguồn master plan |
|---|------------|-------------------|
| 1 | **initGate trước emit SSE** | §2.3 — gate Redis TRƯỚC SSE event |
| 2 | **FSM trong code, không trong prompt** | §5.1.1 — LLM không thể convince transition |
| 3 | **Context block ở cuối payload** | §2.3 — không lưu vào messages array |
| 4 | **CompactSummary = leading user message** | §2.3 — prepend summary, không inject context block |
| 5 | **Independent recovery budgets** | §2.3 — mỗi failure mode counter riêng |
| 6 | **Acceptance criteria không dùng LLM** | §5.3.1 — deterministic file/status checks |
| 7 | **Phantom file prevention** | cancel giữa stream → không flush (trừ stop handshake) |

---

## 5. Constants bổ sung Phase 2

Từ master plan §3 — thêm vào `orchestration/constants.py` nếu chưa có:

### 5.1 Gate (HITL)

| Constant | Giá trị |
|----------|---------|
| `GATE_TTL_SEC` | 1,200 (20 phút) |
| `POLL_INTERVAL_MS` | 300 |
| `MAX_CONSECUTIVE_ERRORS` | 10 |

### 5.2 Tool result caps (pipeline step 6)

| Constant | Mô tả |
|----------|-------|
| `TOOL_RESULT_MAX_CHARS` | Per-tool result cap |
| `HISTORY_CAP_CHARS` | History total cap |
| `TOOL_REJECTED_RESULT` | Sentinel string khi user reject |

### 5.3 Rate limits (§5.8.2)

| Bucket | Limit |
|--------|-------|
| `task_stream` | 100 req/giờ/user |
| `task_create` | 30 tasks/giờ/user |
| `upload` | 30 uploads/giờ/user |
| `dashboard_create` | 20 dashboards/ngày/user |
| `global` | 1000 req/phút hệ thống |

---

## 6. FSM transitions (hardcoded)

**File:** `memory/state_machine.py` — `ALLOWED_TRANSITIONS`:

| From | Allowed to |
|------|------------|
| empty | `create-chat`, `create-dashboard` |
| `create-chat` | `create-dashboard` |
| `create-dashboard` | `edit-dashboard`, `repair-dashboard` |
| `repair-dashboard` | `create-dashboard`, `edit-dashboard` |
| `edit-dashboard` | `edit-dashboard`, `repair-dashboard` |

Invalid transition → `ValueError` với message rõ ràng.

**Không có:** `edit-dashboard` → `create-chat` (không downgrade).

---

## 7. Output files pipeline

| Agent | Output file |
|-------|-------------|
| dashboard-planner | `spec.md` |
| data-binder | `bindings.md` |
| layout-designer | `layout.md` |
| dashboard-builder | `page.tsx` (+ widget files) |
| dashboard-critic | `review.md` |

---

## 8. Mode support

| Mode | Phase 1 | Phase 2 |
|------|---------|---------|
| `auto` | ✅ | ✅ |
| `ask` | ❌ | ✅ — gates cho non-safe tools |

Sub-agent `write_file` trong ask mode → Y/N card ở **cấp task** (không phải agent block).

---

## 9. Cross-references

| File | Tiếp theo |
|------|-----------|
| [01-memory-system.md](./01-memory-system.md) | Implement đầu tiên |
| [11-checklist.md](./11-checklist.md) | DoD cuối phase |
