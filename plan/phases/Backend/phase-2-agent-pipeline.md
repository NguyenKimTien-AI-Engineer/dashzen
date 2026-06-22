# Phase 2 — Full Pipeline & Production Patterns

> **Mục tiêu:** Dashboard pipeline đầy đủ (5 sub-agents + workflow), HITL gates, compaction, artifact buffer, stream resilience.
>
> **Nguồn:** [`01-project-structure-and-techstack.md`](../../01-project-structure-and-techstack.md) §18 P2 + P3, §4–§8, §10–§12, §16, §20
>
> **Ưu tiên:** P1–P2 | **Map §18:** P2 + P3 | **Phụ thuộc:** Phase 1 hoàn thành

---

## 1. Tại sao Phase 2 quan trọng

Phase 1 chứng minh loop + 1 agent. Phase 2 biến DashZen thành **production-grade agent runtime**:

- Chat tự do → `set_memory` → **workflow deterministic** tạo dashboard
- **Ask mode** + Redis gates — user approve tool trước khi chạy
- Context **không blow-up** — 2-tier compaction
- File workspace **an toàn** — artifact buffer, không phantom files
- Stream **resilient** — stop handshake, rate limits, dedup

---

## 2. Deliverables checklist

### 2.1 ③ Memory System (§6)

- [ ] `memory/state_machine.py` — `ALLOWED_TRANSITIONS` enforced
- [ ] `memory/memory_file.py` — đọc/ghi `memory.md` frontmatter
- [ ] `memory/context_block.py` — inject `# MEMORY` / `# USER` / `# WORKFLOW`
- [ ] `set_memory` tool — chuyển `type` + `phase`
- [ ] Sync `Task.type` từ `memory.md.type`
- [ ] Workflow inject mỗi lần `set_memory` (regenerate/resume support)

**FSM transitions:**

```python
("chat", "create-chat") → ("dashboard", "create-dashboard")
("dashboard", "create-dashboard") → edit | repair
("dashboard", "repair-dashboard") → create | edit
("dashboard", "edit-dashboard") → edit | repair
```

### 2.2 ② Agent Registry — full (§5)

**5 specialist agents:**

| Agent | Output |
|-------|--------|
| dashboard-planner | `spec.md` |
| data-binder | `bindings.md` |
| layout-designer | `layout.md` |
| dashboard-builder | `page.tsx`, widgets |
| dashboard-critic | `review.md` |

- [ ] Load tất cả `prompts/agents/*.md`
- [ ] Load workflows:

```
workflows/dashboard/create-dashboard.md
workflows/dashboard/edit-dashboard.md
workflows/dashboard/repair-dashboard.md
workflows/chat/create-chat.md
```

- [ ] Frontmatter validation: tools, maxTurns, outputSchema

### 2.3 ① Orchestration — full (§4)

**Workflow execution:**

```
set_memory({type: dashboard, phase: create-dashboard})
  → spawn dashboard-planner → spec.md
  → spawn data-binder → bindings.md
  → spawn layout-designer → layout.md
  → spawn dashboard-builder → page.tsx
  → spawn dashboard-critic → review.md (pass/fail → repair)
```

- [ ] `workflow.py` — spawn sequence + acceptance criteria
- [ ] `recovery.py` — `append_recovery_messages()` per failure mode
- [ ] Retry budget riêng per recovery path
- [ ] `compaction_exhausted` flag
- [ ] `exec_parallel.py` — batch tool execution delegate Tool System
- [ ] Spawn contract enforce: Status DONE|WAIT|FAIL + Summary ≤ 4KB
- [ ] `AgentRun.activities` — max 200 entries, result cap 2KB/entry
- [ ] Title generation — race-safe `UPDATE ... WHERE title IS NULL`

### 2.4 ④ Tool System — full pipeline (§7)

**Execution pipeline (thứ tự cố định):**

```
validate args (JSON Schema)
  → loop detection (warn @3, block @5)
  → read cache dedup (ReadCache, invalidate on write)
  → gate (ask mode → Gate System ⑦)
  → execute handler
  → truncate result (per-tool cap + history cap 100k)
  → error envelope chuẩn
```

- [ ] `registry.py` — tiers: `READ_ONLY`, `ASK_BYPASS`, `VISIBLE`, `CONCURRENT_SAFE`, `MAIN_TOOLS`, `AGENT_TOOLS`
- [ ] `pipeline.py`, `loop_detection.py`, `partition.py`, `read_cache.py`
- [ ] `packages/tools/orchestration/` — `spawn_agent`, `set_memory`, `ask_user`
- [ ] `packages/tools/data/` — `schema_inspector`, `csv_preview` (basic)
- [ ] `with_gate()` — wrap sub-agent tools ask mode
- [ ] `partition_batches()` — read parallel max 5, write serial

### 2.5 ⑤ Context System (§8)

- [ ] `history.py` — history prefix ổn định (cache-friendly)
- [ ] `compaction.py` — 2-tier:

| Tier | Trigger | Action |
|------|---------|--------|
| Microcompact | 60% budget | Xóa tool results read-only cũ |
| Summary compact | 80% budget | LLM tóm tắt → message `role: compact` |

- [ ] `thinking_codec.py` — encode/decode extended thinking
- [ ] `accounting.py` — `prompt_tokens` per message, `tokens_per_char`
- [ ] `POST /v1/tasks/{id}/compact` — manual compact
- [ ] Payload assembly: history (Context) + context block (Memory)

### 2.6 ⑦ Gate System — HITL (§10)

| Gate | Trigger | API |
|------|---------|-----|
| Tool gate | Ask mode + non-bypass tool | `POST /gates/tool` |
| Ask gate | `ask_user` tool | `POST /gates/ask` |
| Sub-agent gate | Ask mode + agent tool | Same, route by `gateToAgentId` |

- [ ] `init_gate` **trước** SSE emit — tránh race approve
- [ ] Namespace: `gate:` vs `ask:`
- [ ] CAS `SET_IF_PENDING` — chống double-approve
- [ ] Poll jitter + fail-safe unblock
- [ ] Gate feedback inject vào `tool_result` cho LLM
- [ ] `unregister_all_gates` — stream end / task delete
- [ ] SSE: `main_ask` event cho ask_user form

### 2.7 ⑧ Artifact System — production (§11)

- [ ] `ArtifactBuffer` — in-memory Map per stream
- [ ] Stage `write_file`/`edit_file` → buffer → flush on `stream_done` / interrupt
- [ ] Tránh phantom files khi cancel giữa chừng
- [ ] Overwrite-by-name trong workspace
- [ ] `POST /v1/tasks/{id}/upload` — attachment upload
- [ ] Branch-scoped `get_artifacts` (active branch path)
- [ ] Partial save — flush buffer kể cả khi không có assistant text

### 2.8 ⑨ Streaming — full guards (§12.3–§12.4)

| Guard | Hành vi |
|-------|---------|
| Pending user message reuse | Tránh duplicate LLM run khi retry |
| 5s dedup | Cùng content 5s → short-circuit |
| Lock lost | Abort ghost run |
| Gate + client gone | Abort nếu `pending_user_input` + disconnect |
| Safety net | 10 phút auto-abort orphan lock |
| Stop handshake | abort + `cleanup_done` + `partial_message_id` |

**Rate limiting (Redis buckets):**

| Bucket | Limit |
|--------|-------|
| `task_stream` | 100/hr/user |
| `task_create` | 30/hr/user |
| `upload` | 30/hr/user |
| `dashboard_create` | 20/day/user |
| `global` | 1000/min |

- [ ] Response headers: `X-RateLimit-Remaining`, `Retry-After`
- [ ] SSE events bổ sung: `main_think`

### 2.9 ⑩ Persistence — branching (§13)

- [ ] Message tree `parent_id` — regenerate/edit tạo nhánh mới
- [ ] `GET /messages` trả `branchInfo` cho siblings
- [ ] Message role `compact` — boundary ẩn history cũ
- [ ] `AgentRun` reload cho UI `reconstructAgentCalls()`

**Schemas đầy đủ (plan 04):**

- [ ] `DashboardSpec`, `DataBindingPlan`, `LayoutSpec`
- [ ] `GeneratedPage`, `ReviewResult`

### 2.10 API bổ sung (§16)

| Endpoint | Subsystem |
|----------|-----------|
| `POST /gates/tool` | ⑦ |
| `POST /gates/ask` | ⑦ |
| `POST /compact` | ⑤ |
| `POST /upload` | ⑧ |

---

## 3. Definition of done

Phase 2 hoàn thành khi:

1. User chat → `set_memory(dashboard)` → workflow chạy 5 agents tuần tự
2. Critic fail → `repair-dashboard` workflow retry
3. Ask mode → tool gate → user approve → stream resume
4. `ask_user` form gate hoạt động
5. Context > 60% → microcompact tự động; manual compact API
6. Cancel stream giữa chừng → không có phantom files
7. `POST /stop` → partial message + artifact flush
8. Rate limit 429 với headers đúng
9. Regenerate message tạo branch mới (API + messages tree)
10. FE Phase 2 integrate: gates, thinking, compact, reconnect

---

## 4. Gaps Phase 2 (từ §20)

| Gap | Target |
|-----|--------|
| Gate payloads + CAS + feedback | plan 03 + 06 |
| `set_memory` FSM | plan 03 |
| Sub-agent output parse + activities cap | plan 03 |
| Tool pipeline detail | plan 03 |
| Title generation algorithm | plan 03 |
| Message tree + branch API | plan 06 |
| File model + upload security | plan 06 |
| Rate limit matrix | plan 06 |
| `DashboardSpec` Pydantic full | plan 04 |

---

## 5. Rủi ro & phụ thuộc

| Rủi ro | Mitigation |
|--------|------------|
| Workflow spawn sequence fragile | Acceptance criteria trong workflow .md |
| Gate race conditions | `init_gate` trước SSE |
| Compaction mất context quan trọng | Summary compact giữ key facts |
| 5-agent chain latency | Parallel read tools trong sub-agent |

---

## 6. Tiếp theo

Xem [`phase-3-scale-production.md`](./phase-3-scale-production.md) — RAG, eval, observability, connectors.
