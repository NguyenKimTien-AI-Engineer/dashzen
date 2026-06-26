# 05 — ① Orchestration (Minimal)

> Subsystem điều phối toàn bộ luồng chạy — gọi tất cả subsystem khác, không subsystem nào gọi ngược Orchestration.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.5 | `research/02-leadzen-agent-research.md` (main-run.ts, agent-run.ts, spawn-agent.ts)

**Location:** `packages/agents/src/agents/orchestration/`  
**Phụ thuộc:** [02](./02-llm-system.md), [03](./03-persistence-system.md), [04](./04-streaming-system.md), [06](./06-agent-registry.md), [07](./07-tool-system.md), [08](./08-artifact-system.md)

---

## 1. Mục tiêu

- [ ] 1. `constants.py` — tất cả production constants
- [ ] 2. `RuntimeContext` + `run_task()` entry point
- [ ] 3. `main_loop.py` — async generator core engine
- [ ] 4. `agent_loop.py` — isolated sub-agent loop
- [ ] 5. `spawn.py` — spawn_agent bridge
- [ ] 6. `task_title.py` — concurrent auto-title
- [ ] 7. `exec_parallel.py` — parallel tool batches

---

## 2. Constants

**File:** `packages/agents/src/agents/orchestration/constants.py`

Copy đầy đủ từ [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) §4:

- [ ] 1. `MAX_ITERATIONS` = 40
- [ ] 2. `MAX_AGENTS_PER_TURN` = 3
- [ ] 3. `RECOVERY_LIMIT` = 5
- [ ] 4. `TITLE_FORCE_BY_TURN` = 8
- [ ] 5. `SUBAGENT_MAX_TURNS` = 40
- [ ] 6. `SUBAGENT_TIMEOUT_MS` = 1,080,000
- [ ] 7. `MAX_CONCURRENT_TOOLS` = 5
- [ ] 8. `AGENT_OUTPUT_COMPACT_THRESHOLD` = 4,000
- [ ] 9. `SPAWN_SUMMARY_MAX` = 2,000
- [ ] 10. `ACTIVITY_RESULT_MAX` = 2,000
- [ ] 11. `ACTIVITY_COUNT_MAX` = 200

---

## 3. RuntimeContext & run_task()

**File:** `packages/agents/src/agents/orchestration/runtime.py`

### 3.1 RuntimeContext fields

| Field | Type | Mô tả |
|-------|------|-------|
| `task_id` | UUID | |
| `user_id` | UUID | |
| `db` | AsyncSession | |
| `redis` | Redis client | |
| `artifact_buffer` | ArtifactBuffer | Shared route ↔ main loop |
| `mode` | str | `auto` (Phase 1 only) |
| `thinking_enabled` | bool | Extended thinking flag |
| `user_instructions` | str optional | User preferences |
| `abort_signal` | asyncio.Event | Stop handshake |
| `event_emit` | Callable | Emit SSE events |

### 3.2 run_task() — single entry point

```
run_task(ctx, user_message, parent_id, tools, system_prompt)
  → wiring subsystems
  → main_loop()
  → async generator of events
```

### Checklist runtime

- [ ] 1. API route **chỉ** gọi `run_task()` — không import `main_loop` trực tiếp
- [ ] 2. ArtifactBuffer tạo ở route, pass vào ctx
- [ ] 3. Abort signal shared giữa route và main loop

---

## 4. Main loop

**File:** `packages/agents/src/agents/orchestration/main_loop.py`

Async generator — mỗi iteration `yield` SSE events.

### 4.1 Turn flow (5 bước)

**Bước 1 — Lưu user message**

- [ ] Tạo Message record trong DB ngay đầu turn
- [ ] Nếu dedup guard reuse pre-saved → skip create

**Bước 2 — Load context**

- [ ] Song song: message tree path (root → parent_id)
- [ ] Load `memory.md` từ workspace
- [ ] Build LLM payload prefix từ history
- [ ] Phase 1: chưa context block builder — inject memory.md đơn giản

**Bước 3 — Title generation (concurrent)**

- [ ] Fire-and-forget asyncio task
- [ ] Cheap/fast model (không phải main model)
- [ ] Chạy song song với iteration đầu tiên

**Bước 4 — LLM tool-call loop (max MAX_ITERATIONS)**

Mỗi iteration:

- [ ] Refresh memory content từ ArtifactBuffer (nếu có staged changes)
- [ ] **Phase 1 skip:** compaction — defer Phase 2
- [ ] Build payload = history prefix + context
- [ ] `LLMClient.stream()` → yield `main_text` / `main_think`
- [ ] Collect tool calls từ stream
- [ ] Persist assistant message vào DB
- [ ] `exec_parallel(tool_calls)` → execute tools
- [ ] Persist tool result messages
- [ ] Không có tool calls → iteration done → main loop done
- [ ] **Phase 1 skip:** ask mode rejection handling

**Bước 5 — Kết thúc turn**

- [ ] Flush ArtifactBuffer → DB
- [ ] Remap artifact ownership về final assistant message (basic Phase 1)
- [ ] Finalize title → emit `task_meta` nếu title changed
- [ ] Yield `stream_done`

### 4.2 Abort handling

- [ ] Check `abort_signal` mỗi iteration
- [ ] On abort: flush artifacts staged, yield `stream_done` + `partial_message_id`

---

## 5. Sub-agent loop

**File:** `packages/agents/src/agents/orchestration/agent_loop.py`

Chạy trong một lần `spawn_agent` tool call.

### 5.1 Khác biệt vs main loop

| Aspect | Main loop | Agent loop |
|--------|-----------|------------|
| Persist messages | Yes → DB | No — memory-only list |
| SSE yield | Direct | Via `onEvent` callback |
| Timeout | Stream lock TTL | 18 phút wall-clock |
| Return | stream_done | `AgentRunResult` compact |

### 5.2 AgentRunResult

| Field | Type |
|-------|------|
| `output` | string |
| `tools_used` | list |
| `iterations` | int |
| `timed_out` | bool |

### Checklist agent_loop

- [ ] 1. `asyncio.wait_for` hoặc abort controller — `SUBAGENT_TIMEOUT_MS`
- [ ] 2. Max `SUBAGENT_MAX_TURNS` iterations
- [ ] 3. On abort: `timedOut=True`, return partial output (không raise)
- [ ] 4. Forward events: `agent_text`, `agent_tool`, `agent_result`, etc.

---

## 6. spawn.py — spawn_agent

**File:** `packages/agents/src/agents/orchestration/spawn.py`

Cầu nối main loop ↔ agent loop.

### 6.1 Flow

1. [ ] Lookup agent definition từ registry theo tên
2. [ ] Resolve tool list: `AGENT_TOOLS` subset + frontmatter allowlist/disallowlist
3. [ ] **Phase 1 skip:** `withGate()` wrapper — auto mode only
4. [ ] Emit `agent_start` event
5. [ ] Gọi `agent_run()` — forward events qua callback
6. [ ] Parse Status/Summary từ output
7. [ ] Emit `agent_done` với status + summary
8. [ ] Persist activities JSON → AgentRun (upsert messageId+callId)
9. [ ] Output ≤ 4,000 chars → trả full; > 4,000 → chỉ Status/Summary envelope

### 6.2 Recovery on abort

- [ ] Nếu parent abort (lock lost, restart): persist tool result vào DB từ spawn.py
- [ ] Task history intact khi client reconnect

### 6.3 MAX_AGENTS_PER_TURN

- [ ] Đếm spawn calls trong turn
- [ ] Call thứ 4+ → error message ngay, không execute

---

## 7. Auto-title generation

**File:** `packages/agents/src/agents/orchestration/task_title.py`

### 7.1 Behavior

- [ ] Chạy concurrent với main loop turn đầu tiên
- [ ] Cheap/fast model
- [ ] Turns 1–7: model có thể trả `null` nếu intent chưa rõ
- [ ] Turn 8+ (`TITLE_FORCE_BY_TURN`): bắt buộc đặt tên
- [ ] Persist: `UPDATE tasks SET title = ? WHERE id = ? AND title IS NULL`
- [ ] User rename không bị overwrite

### 7.2 SSE

- [ ] Title changed → emit `task_meta` với `title`

---

## 8. Parallel tool execution

**File:** `packages/agents/src/agents/orchestration/exec_parallel.py`

### 8.1 Flow

- [ ] Nhận list tool calls từ main loop
- [ ] `partition_batches()` ([07-tool-system.md](./07-tool-system.md))
- [ ] CONCURRENT_SAFE batch: max `MAX_CONCURRENT_TOOLS` parallel
- [ ] Non-safe batch: serial execution
- [ ] Return `Map[tool_call_id, result]`
- [ ] Handle `overflowAgentIds` — spawn vượt cap → error message

### 8.2 Phase 1 execution

- [ ] Execute tool trực tiếp (không qua 6-step pipeline — Phase 2)
- [ ] try/except → error envelope, không crash stream

---

## 9. System prompts Phase 1

**Files:** `packages/agents/prompts/system/`

- [ ] 1. `system-main.md` — orchestrator persona + operating contract
- [ ] 2. `system-agent.md` — sub-agent worker identity + security rules
- [ ] 3. Main loop load `system-main.md` via registry loader

---

## 10. Definition of done — step 05

- [ ] `run_task()` end-to-end với mock LLM (hoặc Ollama)
- [ ] Main loop yield `main_text` events
- [ ] `spawn_agent("dashboard-planner")` → agent events sequence
- [ ] Agent loop timeout không crash server
- [ ] Auto-title set sau turn 1 (hoặc turn 8 force)
- [ ] Abort signal stops loop + flushes artifacts

---

## 11. Cross-references

| File | Liên quan |
|------|-----------|
| [06-agent-registry.md](./06-agent-registry.md) | Agent lookup |
| [07-tool-system.md](./07-tool-system.md) | Tool execution |
| [08-artifact-system.md](./08-artifact-system.md) | Flush on done |
| `research/02-leadzen` | main-run.ts, agent-run.ts |
