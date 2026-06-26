# 06 — ⑦ Gate System — Full HITL

> Human-in-the-loop — user kiểm soát từng tool call trong ask mode. initGate **trước** emit SSE.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.6 | §2.3 nguyên tắc initGate

**Location:** `packages/agents/src/agents/gates/`  
**Phụ thuộc:** [Phase 1 04-streaming](../phase-1/04-streaming-system.md) (Redis), [10-api-layer-extensions](./10-api-layer-extensions.md)

---

## 1. Mục tiêu

- [ ] 1. `gate_service.py` — Redis-backed polling, Lua CAS
- [ ] 2. Tool gate namespace `gate:{task_id}:{call_id}`
- [ ] 3. Ask gate namespace `ask:{task_id}:{call_id}`
- [ ] 4. `unregister_all_gates()` cleanup in stream finally
- [ ] 5. In-memory fallback cho dev without Redis

---

## 2. Gate service core

**File:** `packages/agents/src/agents/gates/gate_service.py`

### 2.1 Constants

| Constant | Value |
|----------|-------|
| `GATE_TTL_SEC` | 1,200 (20 phút) — orphan cleanup, không behavioral timeout |
| `POLL_INTERVAL_MS` | 300 |
| `MAX_CONSECUTIVE_ERRORS` | 10 — fail-safe unblock |

---

## 3. Tool gate flow

### Bước 1 — init_gate(task_id, call_id)

- [ ] `SET gate:{task_id}:{call_id} "pending" NX EX {GATE_TTL_SEC}`
- [ ] **NX** — không overwrite nếu đã tồn tại
- [ ] **PHẢI xảy ra TRƯỚC emit SSE** — tránh race: client approve trước khi gate exists

### Bước 2 — Emit SSE

- [ ] Emit `main_tool` event → FE hiển thị Y/N approval card

### Bước 3 — register_gate(task_id, call_id, signal)

- [ ] Poll Redis key mỗi 300ms + random jitter (tránh thundering herd)
- [ ] `pending` → continue poll
- [ ] `approved` / `rejected` → resolve
- [ ] Key không tồn tại (expired TTL) → resolve as **rejected**
- [ ] Redis lỗi 10 lần liên tiếp → **fail-safe unblock** (không treo stream)

### Bước 4 — resolve_gate (user action)

**Endpoint:** `POST /gates/tool` — xem [10-api-layer-extensions.md](./10-api-layer-extensions.md)

- [ ] Lua atomic `SET_IF_PENDING` — chỉ set nếu current = `"pending"`
- [ ] Ngăn double-approve concurrent requests

### 2.5 Feedback mechanism

| User action | LLM sees |
|-------------|----------|
| Reject + feedback text | Feedback injected vào tool result content |
| Approve + feedback text | Feedback appended sau execution result |

---

## 4. Ask gate (separate namespace)

### 4.1 Namespace

`ask:{task_id}:{call_id}` — tách biệt tool gate.

### 4.2 ask_user tool flow

1. [ ] `ask_user` tool trigger ask gate
2. [ ] Emit `main_ask` SSE với câu hỏi
3. [ ] Block poll `register_ask_gate()`
4. [ ] User submit `POST /gates/ask`
5. [ ] Store answer in Redis → unblock
6. [ ] Return answer to LLM as tool result

### 4.3 API

| Endpoint | Mô tả |
|----------|-------|
| `POST /v1/tasks/{id}/gates/tool` | Approve/reject tool call |
| `POST /v1/tasks/{id}/gates/ask` | Submit ask answer |

---

## 5. Gate cleanup

### 5.1 unregister_all_gates(task_id)

Gọi trong `finally` block stream route:

- [ ] 1. Scan Redis keys `gate:{task_id}:*`
- [ ] 2. Scan Redis keys `ask:{task_id}:*`
- [ ] 3. Delete tất cả
- [ ] 4. Ngăn orphan gate keys khi stream kết thúc đột ngột

---

## 6. In-memory fallback (dev)

Khi không có Redis:

- [ ] 1. Module-level dict singleton (survive hot-reload)
- [ ] 2. Same API: init_gate, register_gate, resolve_gate
- [ ] 3. Poll in-memory dict thay Redis

---

## 7. withGate() wrapper

**File:** `packages/agents/src/agents/orchestration/spawn.py` hoặc `gates/wrapper.py`

```python
# Conceptual
async def withGate(tool_fn, task_id, call_id, mode):
    if mode != "ask" or tool in ASK_BYPASS:
        return await tool_fn()
    init_gate(task_id, call_id)  # BEFORE any SSE
    emit main_tool
    decision = await register_gate(...)
    if rejected: return TOOL_REJECTED_RESULT
    return await tool_fn()
```

- [ ] 1. Transparent wrapper cho non-safe tools
- [ ] 2. Sub-agent write_file → gate at **task level**

---

## 8. Integration checklist

- [ ] 1. Pipeline step 4 calls gate_service ([04](./04-tool-system-full-pipeline.md))
- [ ] 2. Stream route finally calls `unregister_all_gates`
- [ ] 3. init_gate always before SSE emit
- [ ] 4. TOOL_REJECTED_RESULT returned on reject

---

## 9. Definition of done — step 06

- [ ] Ask mode write_file → main_tool → approve → file written
- [ ] Reject → TOOL_REJECTED_RESULT → main loop stops after flush
- [ ] ask_user → main_ask → submit answer → agent continues
- [ ] Double-approve blocked by Lua CAS
- [ ] Stream end cleans all gate keys
- [ ] Sub-agent write_file shows Y/N at task level

---

## 10. Cross-references

| File | Liên quan |
|------|-----------|
| [04-tool-system-full-pipeline.md](./04-tool-system-full-pipeline.md) | Pipeline step 4 |
| [10-api-layer-extensions.md](./10-api-layer-extensions.md) | Gate HTTP endpoints |
| `research/02-leadzen` | gate-service.ts reference |
