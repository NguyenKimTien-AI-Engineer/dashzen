# 03 — ① Orchestration — Full Pipeline

> Workflow execution engine deterministic + LLM recovery paths + exec_parallel full.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.3

**Location:** `packages/agents/src/agents/orchestration/`  
**Phụ thuộc:** [01](./01-memory-system.md), [02](./02-agent-registry-and-workflows.md), [06](./06-gate-system-hitl.md), [05](./05-context-system-compaction.md)

---

## 1. Mục tiêu

- [ ] 1. `workflow.py` — deterministic 5-agent pipeline engine
- [ ] 2. `recovery.py` — LLM failure recovery message injection
- [ ] 3. `exec_parallel.py` — full: overflowAgentIds + TOOL_REJECTED_RESULT
- [ ] 4. `spawn.py` — `withGate()` wrapper cho ask mode
- [ ] 5. `main_loop.py` — wire compaction, context block, workflow takeover

---

## 2. Workflow execution engine

**File:** `packages/agents/src/agents/orchestration/workflow.py`

### 2.1 Trigger

Khi Memory FSM chuyển sang phase `create-dashboard`:

- [ ] `workflow.py` **take over** — không để main loop spawn agent tùy ý
- [ ] Đọc `prompts/workflows/dashboard/create-dashboard.md`
- [ ] Parse spawn sequence

### 2.2 Execution flow

```
spawn planner → wait result → validate acceptance
  → spawn binder → validate
  → spawn designer → validate
  → spawn builder → validate
  → spawn critic → read review.md
  → FAIL → repair-dashboard workflow
  → PASS → done
```

### 2.3 Acceptance criteria validation

**Deterministic checks — KHÔNG dùng LLM validate:**

- [ ] 1. Output file tồn tại? (spec.md, bindings.md, etc.)
- [ ] 2. Agent Status là DONE?
- [ ] 3. Summary không chứa lỗi nghiêm trọng?
- [ ] 4. review.md critic: PASS/FAIL parse

### 2.4 Repair flow

- [ ] Critic FAIL → chuyển `repair-dashboard` workflow
- [ ] Đọc review.md issues
- [ ] Minor → builder edit; fundamental → restart planner

### 2.5 Edit dashboard flow

- [ ] Phase `edit-dashboard` → planner reads old spec + user request
- [ ] Pipeline continues from binder

---

## 3. LLM recovery paths

**File:** `packages/agents/src/agents/orchestration/recovery.py`

### 3.1 append_recovery_messages(messages, text, thinking, ...)

Inject cặp messages (assistant partial + user continuation) để retry.

| Failure mode | Recovery message |
|--------------|------------------|
| max_tokens (cắt giữa chừng) | "please continue from where you left off" |
| empty response | "please respond to the request" |
| thinking-only | "please include your response text" |

### 3.2 Independent recovery budgets

- [ ] 1. Mỗi failure mode có counter riêng
- [ ] 2. `RECOVERY_LIMIT` = 5 per path
- [ ] 3. Recovery injection **KHÔNG** thay đổi `MAX_ITERATIONS` counter
- [ ] 4. Chỉ tăng counter riêng của từng path

### 3.3 Wire vào main_loop + agent_loop

- [ ] Detect failure mode sau LLM stream
- [ ] Call `append_recovery_messages()` nếu under recovery limit
- [ ] Retry iteration

---

## 4. exec_parallel.py — Full implementation

Bổ sung so với Phase 1:

### 4.1 overflowAgentIds

- [ ] 1. Đếm `spawn_agent` calls trong turn
- [ ] 2. Calls vượt `MAX_AGENTS_PER_TURN` (3) → error message ngay
- [ ] 3. Không execute overflow spawns

### 4.2 TOOL_REJECTED_RESULT

- [ ] 1. Sentinel string constant
- [ ] 2. Khi user reject tool trong ask mode → tool returns sentinel
- [ ] 3. Main loop detect sentinel → dừng loop ngay sau flush artifacts

---

## 5. spawn.py — withGate() pattern

### 5.1 Ask mode wrapping

Khi `mode=ask`:

- [ ] 1. Wrap từng **non-safe** tool bằng `withGate()`
- [ ] 2. Transparent wrapper — pause để user approve trước execute
- [ ] 3. Read-only tools bypass gate
- [ ] 4. `ASK_BYPASS` tools bypass gate

### 5.2 Sub-agent ask mode

- [ ] Sub-agent `write_file` trong ask mode → Y/N card ở **cấp task** (main loop level)
- [ ] Không phải cấp agent block

### 5.3 Recovery on abort (giữ Phase 1)

- [ ] Parent abort → persist tool result từ spawn.py
- [ ] Task history intact khi reconnect

---

## 6. main_loop.py updates

### 6.1 Wire Phase 2 subsystems

- [ ] 1. `build_context_block()` mỗi iteration ([01](./01-memory-system.md))
- [ ] 2. `compact_if_over_budget()` đầu mỗi iteration ([05](./05-context-system-compaction.md))
- [ ] 3. `build_history()` thay flat message load ([05](./05-context-system-compaction.md))
- [ ] 4. Tool calls qua 6-step pipeline ([04](./04-tool-system-full-pipeline.md))
- [ ] 5. Detect `TOOL_REJECTED_RESULT` → stop after flush

### 6.2 Workflow takeover hook

- [ ] Khi memory phase = `create-dashboard` | `edit-dashboard` | `repair-dashboard`
- [ ] Delegate spawn sequence to `workflow.py`
- [ ] Main loop vẫn owns SSE emit + persistence

### 6.3 flush_and_remap

- [ ] End of turn: `ArtifactBuffer.flush_and_remap()` ([07](./07-artifact-and-upload.md))

---

## 7. agent_loop.py updates

- [ ] 1. Tools qua pipeline (gates apply at task level for sub-agent writes)
- [ ] 2. Recovery paths với `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT` = 3
- [ ] 3. Forward events unchanged

---

## 8. Definition of done — step 03

- [ ] `create-dashboard` workflow spawns 5 agents tuần tự
- [ ] Acceptance criteria block bad steps
- [ ] Critic FAIL triggers repair-dashboard
- [ ] Recovery retries on max_tokens without eating MAX_ITERATIONS
- [ ] Ask mode withGate pauses non-safe tools
- [ ] TOOL_REJECTED_RESULT stops main loop

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [01-memory-system.md](./01-memory-system.md) | FSM triggers workflow |
| [04-tool-system-full-pipeline.md](./04-tool-system-full-pipeline.md) | Pipeline execution |
| [06-gate-system-hitl.md](./06-gate-system-hitl.md) | withGate implementation |
| `research/02-leadzen` | main-run.ts workflow patterns |
