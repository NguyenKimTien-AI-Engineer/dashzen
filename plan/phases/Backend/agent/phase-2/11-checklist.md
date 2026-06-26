# 11 — Checklist & Definition of Done

> Checklist cuối Phase 2 — **phải PASS toàn bộ 15 items** trước khi bắt đầu Phase 3.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.10

---

## 1. Definition of Done (15 items)

Copy đầy đủ từ master plan:

- [ ] **1.** Gửi *"tạo dashboard doanh thu theo khu vực"* → `set_memory({type: dashboard, phase: create-dashboard})` được gọi → workflow file được inject → **5 agents spawn tuần tự**
- [ ] **2.** Mỗi agent ghi đúng output file: planner → `spec.md`, binder → `bindings.md`, designer → `layout.md`, builder → `page.tsx`, critic → `review.md`
- [ ] **3.** dashboard-critic trả FAIL → orchestrator tự động chuyển sang `repair-dashboard` workflow và retry
- [ ] **4.** Bật ask mode → agent gọi `write_file` → `main_tool` event xuất hiện trên UI → user click Approve → file được ghi, stream tiếp tục
- [ ] **5.** Agent gọi `ask_user("bạn muốn dùng loại chart nào?")` → `main_ask` event → user submit answer → agent nhận answer và tiếp tục
- [ ] **6.** Conversation đủ dài → context tự động microcompact khi vượt 60%; tự động summary compact khi vượt 80%; `POST /compact` hoạt động manually
- [ ] **7.** User cancel stream giữa lúc builder đang viết page.tsx → file **KHÔNG** xuất hiện trong artifacts (phantom file prevention)
- [ ] **8.** `POST /stop` → nhận `stream_done` với `partial_message_id`; `GET /artifacts` trả files đã được flush trước khi stop
- [ ] **9.** Rate limit: send >100 stream requests trong 1 giờ → nhận **429** với đúng headers
- [ ] **10.** Regenerate assistant message → tạo nhánh mới; `GET /messages` trả `branch_info`; có thể switch giữa nhánh
- [ ] **11.** `GET /messages` của task đã có agent run → trả activities timeline cho mỗi spawn
- [ ] **12.** Sub-agent gọi `write_file` trong ask mode → Y/N card xuất hiện ở **cấp task** (không phải cấp agent block)
- [ ] **13.** Nếu stream lock bị mất (simulate server restart) → partial agent result được persist, task history intact khi reload
- [ ] **14.** Loop detection: agent gọi cùng `read_file` 3 lần → warn; 5 lần → block với message rõ ràng
- [ ] **15.** Upload file CSV → xuất hiện trong artifacts với `source=upload`

---

## 2. Per-step verification map

| DoD # | Step plan | Subsystem |
|-------|-----------|-----------|
| 1–3 | [03](./03-orchestration-full-pipeline.md) + [01](./01-memory-system.md) + [02](./02-agent-registry-and-workflows.md) | Workflow pipeline |
| 2 | [02](./02-agent-registry-and-workflows.md) | 5 agents output |
| 3 | [03](./03-orchestration-full-pipeline.md) | Repair workflow |
| 4, 12 | [06](./06-gate-system-hitl.md) + [04](./04-tool-system-full-pipeline.md) | HITL gates |
| 5 | [04](./04-tool-system-full-pipeline.md) + [10](./10-api-layer-extensions.md) | ask_user |
| 6 | [05](./05-context-system-compaction.md) + [10](./10-api-layer-extensions.md) | Compaction |
| 7–8 | [07](./07-artifact-and-upload.md) | Phantom prevention |
| 9 | [08](./08-streaming-and-rate-limits.md) | Rate limits |
| 10–11 | [09](./09-persistence-branching.md) | Branching |
| 13 | [03](./03-orchestration-full-pipeline.md) | Abort recovery |
| 14 | [04](./04-tool-system-full-pipeline.md) | Loop detection |
| 15 | [07](./07-artifact-and-upload.md) + [10](./10-api-layer-extensions.md) | Upload |

---

## 3. Test cases chi tiết

### 3.1 Full 5-agent pipeline (DoD #1–2)

**Input:** `"tạo dashboard doanh thu theo khu vực"`  
**Mode:** `auto`

**Expected sequence:**
1. `set_memory({type: dashboard, phase: create-dashboard})`
2. Workflow inject `create-dashboard.md`
3. `agent_start` dashboard-planner → `spec.md`
4. `agent_start` data-binder → `bindings.md`
5. `agent_start` layout-designer → `layout.md`
6. `agent_start` dashboard-builder → `page.tsx`
7. `agent_start` dashboard-critic → `review.md` PASS
8. `stream_done`

**Verify:** `GET /artifacts` has all 5 files with correct content.

### 3.2 Critic FAIL → repair (DoD #3)

- [ ] 1. Force or mock critic FAIL in review.md
- [ ] 2. Orchestrator transitions to `repair-dashboard`
- [ ] 3. Retry pipeline per repair workflow rules

### 3.3 Ask mode HITL (DoD #4, #12)

- [ ] 1. `mode: ask` stream request
- [ ] 2. Agent calls `write_file` → `main_tool` SSE
- [ ] 3. `POST /gates/tool` approve
- [ ] 4. File written, stream continues
- [ ] 5. Sub-agent write_file → Y/N at task level (not agent block)

### 3.4 ask_user (DoD #5)

- [ ] 1. Agent calls `ask_user("bạn muốn dùng loại chart nào?")`
- [ ] 2. `main_ask` SSE
- [ ] 3. `POST /gates/ask` with answer
- [ ] 4. Agent receives answer in tool result

### 3.5 Compaction (DoD #6)

- [ ] 1. Long conversation exceeds 60% → microcompact triggers
- [ ] 2. Exceeds 80% → summary compact + role=compact message in DB
- [ ] 3. `POST /compact` manual → returns summary

### 3.6 Phantom files (DoD #7)

- [ ] 1. Start dashboard build (builder phase)
- [ ] 2. Kill client / abort without stop handshake
- [ ] 3. `GET /artifacts` → **no** page.tsx

### 3.7 Stop handshake (DoD #8)

- [ ] 1. `POST /stop` during active stream
- [ ] 2. `stream_done` + `partial_message_id`
- [ ] 3. `GET /artifacts` → files flushed before stop point

### 3.8 Rate limit (DoD #9)

- [ ] 1. Send 101 stream requests in 1 hour (same user)
- [ ] 2. 101st → HTTP 429
- [ ] 3. Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

### 3.9 Branching (DoD #10)

- [ ] 1. Regenerate assistant message
- [ ] 2. New branch created (same parent_id)
- [ ] 3. `GET /messages` → `branch_info.sibling_count` > 1
- [ ] 4. Stream with different `parent_id` → different branch history

### 3.10 AgentRun reload (DoD #11)

- [ ] 1. Complete task with agent spawns
- [ ] 2. Reload page / `GET /messages`
- [ ] 3. `agent_runs[].activities` timeline visible per spawn

### 3.11 Lock loss recovery (DoD #13)

- [ ] 1. Simulate server restart during agent run
- [ ] 2. Partial agent result persisted
- [ ] 3. `GET /messages` history intact

### 3.12 Loop detection (DoD #14)

- [ ] 1. Agent calls identical `read_file` 3× → warning in result
- [ ] 2. 5× → blocked with clear error message

### 3.13 Upload (DoD #15)

- [ ] 1. `POST /upload` with CSV file
- [ ] 2. `GET /artifacts` → file with `source: upload`

---

## 4. File map Phase 2 → Code (new/modified)

Từ master plan §10 — Phase 2 files:

### packages/agents/ (new)

| File | Step |
|------|------|
| `memory/state_machine.py` | 01 |
| `memory/memory_file.py` | 01 |
| `memory/context_block.py` | 01 |
| `orchestration/workflow.py` | 03 |
| `orchestration/recovery.py` | 03 |
| `tools/pipeline.py` | 04 |
| `context/history.py` | 05 |
| `context/compaction.py` | 05 |
| `context/accounting.py` | 05 |
| `context/thinking_codec.py` | 05 |
| `gates/gate_service.py` | 06 |
| `streaming/rate_limit.py` | 08 |
| `streaming/guards.py` | 08 (extend) |

### packages/tools/ (new)

| File | Step |
|------|------|
| `file/edit_file.py` | 04 |
| `orchestration/set_memory.py` | 01 |
| `orchestration/ask_user.py` | 04 |
| `data/schema_inspector.py` | 04 |
| `data/csv_preview.py` | 04 |

### packages/agents/prompts/ (new)

| File | Step |
|------|------|
| `agents/data-binder.md` | 02 |
| `agents/layout-designer.md` | 02 |
| `agents/dashboard-builder.md` | 02 |
| `agents/dashboard-critic.md` | 02 |
| `workflows/chat/create-chat.md` | 02 |
| `workflows/dashboard/create-dashboard.md` | 02 |
| `workflows/dashboard/edit-dashboard.md` | 02 |
| `workflows/dashboard/repair-dashboard.md` | 02 |

### apps/api/ (new routes)

| File | Step |
|------|------|
| `routes/gates.py` | 10 |
| `routes/upload.py` | 10 |
| `routes/compact.py` | 10 |

---

## 5. Gate sang Phase 3

Phase 3 **không bắt đầu** until:

- [ ] Tất cả 15 DoD items PASS
- [ ] Phase 1 regression — 13 items still pass
- [ ] No phantom files on cancel tests
- [ ] Document known limitations

**Phase 3 adds:** Observability (structlog production, OTEL, eval CI), export zip, security hardening, real schema introspection.

---

## 6. Implementation order (tóm tắt)

```
00 Verify Phase 1 gate (13/13)
01 Memory FSM + set_memory
02 5 agents + 4 workflows
06 Gates (before pipeline step 4)
04 Tool 6-step pipeline + new tools
05 Context compaction
03 Orchestration workflow + recovery
07 Artifact flush_and_remap + upload
08 Rate limits + guards
09 Persistence branching
10 API extensions
11 E2E — 15 items
```

---

## 7. Cross-references

| File | Liên quan |
|------|-----------|
| [README.md](./README.md) | Phase 2 overview |
| [phase-1/10-checklist.md](../phase-1/10-checklist.md) | Prerequisite |
| [`00-master-agent-plan.md`](../00-master-agent-plan.md) §6 | Phase 3 scope |
