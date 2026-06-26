# 01 — ③ Memory System

> Bộ não workflow của task — lưu phase hiện tại và inject workflow instructions vào payload LLM mỗi turn.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.1

**Location:** `packages/agents/src/agents/memory/`  
**Phụ thuộc:** [Phase 1](../phase-1/) ArtifactBuffer, registry loader

---

## 1. Mục tiêu

- [ ] 1. `WorkflowFSM` — `ALLOWED_TRANSITIONS` hardcoded
- [ ] 2. `memory_file.py` — read/write memory.md
- [ ] 3. `context_block.py` — build context block cuối payload
- [ ] 4. `set_memory` tool — gateway duy nhất đổi workflow state
- [ ] 5. `Task.type` sync conditional UPDATE

---

## 2. FSM state machine

**File:** `packages/agents/src/agents/memory/state_machine.py`

### 2.1 WorkflowFSM

`ALLOWED_TRANSITIONS` dict hardcoded:

| From phase | Allowed transitions |
|------------|---------------------|
| empty | `create-chat`, `create-dashboard` |
| `create-chat` | `create-dashboard` |
| `create-dashboard` | `edit-dashboard`, `repair-dashboard` |
| `repair-dashboard` | `create-dashboard`, `edit-dashboard` |
| `edit-dashboard` | `edit-dashboard`, `repair-dashboard` |

### 2.2 Validation

- [ ] 1. `validate_transition(current_phase, new_phase) -> bool`
- [ ] 2. Invalid transition → `ValueError` với message rõ ràng
- [ ] 3. Ví dụ invalid: `edit-dashboard` → `create-chat`
- [ ] 4. **Transition rules trong code — KHÔNG trong prompt** (LLM không thể convince)

### 2.3 MemoryState model

```python
# Conceptual
MemoryState(type: str, phase: str)
```

---

## 3. memory.md file handling

**File:** `packages/agents/src/agents/memory/memory_file.py`

### 3.1 read_memory(db, task_id)

- [ ] 1. Đọc file `memory.md` từ workspace (DB hoặc ArtifactBuffer)
- [ ] 2. Parse YAML frontmatter
- [ ] 3. Trả `MemoryState(type, phase)`

**Format memory.md:**

```yaml
---
type: chat | dashboard
phase: create-chat | create-dashboard | edit-dashboard | repair-dashboard
---
```

### 3.2 write_memory(db, task_id, type, phase, artifact_buffer)

- [ ] 1. Cập nhật memory.md content
- [ ] 2. **Stage vào ArtifactBuffer** — không ghi DB ngay
- [ ] 3. Main loop thấy thay đổi iteration tiếp theo không cần DB round-trip
- [ ] 4. Load và trả workflow content từ `prompts/workflows/{type}/{phase}.md`

---

## 4. Context block builder

**File:** `packages/agents/src/agents/memory/context_block.py`

### 4.1 build_context_block(memory_content, user_instructions)

Tạo LLM message đặc biệt inject vào **CUỐI** payload mỗi turn.

**Cấu trúc markdown 3 phần:**

```markdown
# MEMORY
{nội dung memory.md — type + phase}

# USER
{user preferences/instructions nếu có}

# WORKFLOW
{nội dung file workflow phase hiện tại}
```

### 4.2 Invariants

- [ ] 1. Message này **KHÔNG BAO GIỜ** lưu vào mảng `messages`
- [ ] 2. Rebuild fresh mỗi iteration — phản ánh state mới nhất
- [ ] 3. Giữ history prefix ổn định (cache-friendly với Anthropic prefix caching)

### 4.3 Wire vào main_loop

- [ ] Thay thế Phase 1 inject memory đơn giản
- [ ] Gọi `build_context_block()` mỗi iteration trước LLM call

---

## 5. set_memory tool

**File:** `packages/tools/src/tools/orchestration/set_memory.py`

Gateway **duy nhất** thay đổi workflow state.

### 5.1 Parameters

```json
{ "type": "dashboard", "phase": "create-dashboard" }
```

### 5.2 Execution flow

1. [ ] Validate cả `type` và `phase` không rỗng
2. [ ] `read_memory()` — đọc state hiện tại
3. [ ] `WorkflowFSM.validate_transition()` — FSM check
4. [ ] `write_memory()` — cập nhật memory.md + stage ArtifactBuffer
5. [ ] **Task.type sync** nếu type thay đổi (xem §6)
6. [ ] Emit `task_meta` SSE nếu type changed (FE update task header)
7. [ ] `nameTaskIfUntitled()` fire-and-forget nếu task chưa có title
8. [ ] Load workflow file → **return workflow content** làm tool result (LLM không cần read_file riêng)

### 5.3 Tool tier

- [ ] Add vào `ASK_BYPASS` (orchestration tool — không Y/N card)
- [ ] Add vào `MAIN_TOOLS` only — **không** trong `AGENT_TOOLS`

---

## 6. Task.type sync

Khi memory.md type upgrade `chat` → `dashboard`:

```sql
UPDATE tasks
SET type = 'dashboard'
WHERE id = :task_id
  AND (type IS NULL OR type = 'chat')
```

- [ ] 1. Conditional UPDATE — không overwrite nếu đã production type
- [ ] 2. Không downgrade type
- [ ] 3. Trigger `dashboard_create` rate limit bucket khi type → dashboard

---

## 7. Integration với workflow engine

- [ ] 1. Khi `set_memory` → phase `create-dashboard` → workflow engine take over ([03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md))
- [ ] 2. Critic FAIL → `set_memory` hoặc workflow auto → `repair-dashboard`
- [ ] 3. Workflow content trong tool result hướng dẫn orchestrator spawn sequence

---

## 8. Definition of done — step 01

- [ ] FSM rejects invalid transitions với ValueError
- [ ] `set_memory({type: dashboard, phase: create-dashboard})` → memory.md updated + workflow returned
- [ ] `task_meta` SSE emitted khi type changes
- [ ] Context block append cuối payload, không trong messages DB
- [ ] Task.type synced chat → dashboard

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [02-agent-registry-and-workflows.md](./02-agent-registry-and-workflows.md) | Workflow files loaded |
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | workflow.py takeover |
| `research/02-leadzen` | set-memory FSM reference |
