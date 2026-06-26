# 04 — ⑨ Streaming System (Core)

> Vận chuyển events từ agent loop về client qua SSE — schema single source of truth, stream lock per task.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.4 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.9

**Location:** `packages/agents/src/agents/streaming/`  
**Phụ thuộc:** [01-infra-and-monorepo.md](./01-infra-and-monorepo.md) (Redis)

---

## 1. Mục tiêu

- [ ] 1. Pydantic SSE event schema — single source of truth FE + BE
- [ ] 2. Redis stream lock acquire/release/heartbeat
- [ ] 3. EventBus internal pub/sub (`asyncio.Queue`)
- [ ] 4. Guards cơ bản: pending reuse, dedup, stop handshake, orphan lock safety-net

---

## 2. SSE Event Schema

**File:** `packages/agents/src/agents/streaming/events.py`

### 2.1 Main loop events

| Event type | Payload chính | UI behavior |
|------------|---------------|-------------|
| `main_text` | `delta: string` | Streaming orchestrator text |
| `main_think` | `delta: string` | Extended thinking (Anthropic) |
| `main_tool` | `call_id`, `name`, `args` | Activity chip — tool bắt đầu |
| `main_result` | `call_id`, `status`, `result` | Tool kết quả (success/rejected/error) |
| `main_ask` | `call_id`, `question` | Form input — **Phase 2** (schema sẵn) |

### 2.2 Sub-agent events

| Event type | Payload chính | UI behavior |
|------------|---------------|-------------|
| `agent_start` | `call_id`, `name`, `displayName` | Mở agent block |
| `agent_text` | `call_id`, `delta` | Text trong agent block |
| `agent_think` | `call_id`, `delta` | Thinking trong agent block |
| `agent_tool` | `call_id`, `tool_call_id`, `name`, `args` | Tool trong agent block |
| `agent_result` | `call_id`, `tool_call_id`, `status`, `result` | Tool result trong agent block |
| `agent_done` | `call_id`, `status`, `summary` | Đóng agent block |

### 2.3 Lifecycle events

| Event type | Payload chính | UI behavior |
|------------|---------------|-------------|
| `file_artifact` | `name`, `content`, `kind` | Canvas preview trigger |
| `task_meta` | `title?`, `type?` | Update task header |
| `heartbeat` | `{}` | Keep-alive — **KHÔNG** dùng tên `ping` |
| `stream_done` | `partial_message_id?` | Stream kết thúc thành công |
| `stream_error` | `message` | User-friendly error |

### 2.4 Checklist schema

- [ ] 1. Mỗi event có field `type` discriminator
- [ ] 2. Export `MainStreamEvent = Union[...]` type alias
- [ ] 3. `serialize_event(event) -> str` → `data: <json>\n\n`
- [ ] 4. FE contract document trong event docstrings
- [ ] 5. Pydantic v2 `model_dump_json()` compatible

---

## 3. Stream Lock

**File:** `packages/agents/src/agents/streaming/lock.py`

### 3.1 Acquire

- [ ] 1. Redis `SET lock:stream:{task_id} {token} NX EX {LOCK_TTL_SEC}`
- [ ] 2. Token = UUID random per stream
- [ ] 3. Lock đã tồn tại → raise `StreamLockError` → route trả **409**
- [ ] 4. In-memory fallback: module-level dict singleton khi không có Redis

### 3.2 Heartbeat refresh

- [ ] 1. Background asyncio task refresh TTL mỗi `LOCK_REFRESH_INTERVAL_MS` (20s)
- [ ] 2. `EXPIRE lock:stream:{task_id} {LOCK_TTL_SEC}` nếu token match
- [ ] 3. Cancel heartbeat khi stream kết thúc

### 3.3 Release

- [ ] 1. Lua compare-and-delete: chỉ xóa nếu value == token
- [ ] 2. Ngăn stream cũ vô tình xóa lock của stream mới
- [ ] 3. Gọi trong `finally` block của stream route

### 3.4 Constants

| Constant | Value |
|----------|-------|
| `LOCK_TTL_SEC` | 90 |
| `LOCK_REFRESH_INTERVAL_MS` | 20,000 |

---

## 4. EventBus

**File:** `packages/agents/src/agents/streaming/event_bus.py`

### 4.1 Design

- Internal pub/sub giữa agent loop và stream route
- `asyncio.Queue` — producer put, consumer get trong async for
- **Không persist** events — ephemeral transport

### 4.2 API

| Method | Mô tả |
|--------|-------|
| `emit(event: MainStreamEvent)` | Agent loop gọi |
| `async for event in bus:` | Stream route consume |
| `close()` | Signal end of stream |

### 4.3 Checklist

- [ ] 1. Thread-safe trong single event loop
- [ ] 2. Backpressure: queue maxsize reasonable (e.g. 1000)
- [ ] 3. `close()` unblock consumer waiting on empty queue

---

## 5. Stream resilience guards

**File:** `packages/agents/src/agents/streaming/guards.py`

### 5.1 Pending message reuse

Trước khi tạo user message mới:

- [ ] 1. Check task có user message "orphaned" (không có assistant response)
- [ ] 2. Nếu content giống request hiện tại → reuse message ID
- [ ] 3. Tránh duplicate LLM run khi client retry

### 5.2 5-second dedup

- [ ] 1. Track `(task_id, content_hash, timestamp)` tuples in-memory
- [ ] 2. Exact same content trong 5s → short-circuit, không gọi LLM
- [ ] 3. Trả 200 với indicator deduplicated (optional)

### 5.3 Safety-net orphan lock monitor

- [ ] 1. Background task scan periodically (mỗi vài phút)
- [ ] 2. Lock tồn tại nhưng heartbeat không refresh → auto-release
- [ ] 3. Cover server crash scenario

### 5.4 Stop handshake

- [ ] 1. `POST /stop` set abort signal (asyncio.Event hoặc Redis flag)
- [ ] 2. Main loop nhận signal → dừng iteration
- [ ] 3. Flush artifacts đã stage
- [ ] 4. Yield `stream_done` kèm `partial_message_id`
- [ ] 5. Client dùng `partial_message_id` hiển thị partial response

### 5.5 Client disconnect behavior

- [ ] 1. Client ngắt SSE connection → **KHÔNG** cancel LLM call
- [ ] 2. Main loop tiếp tục chạy → persist messages đầy đủ
- [ ] 3. Reconnect `GET /messages` thấy kết quả hoàn chỉnh

---

## 6. SSE wire format

```
data: {"type":"main_text","delta":"Hello"}\n\n
data: {"type":"heartbeat"}\n\n
data: {"type":"stream_done"}\n\n
```

- [ ] 1. `Content-Type: text/event-stream`
- [ ] 2. `Cache-Control: no-cache`
- [ ] 3. `Connection: keep-alive`
- [ ] 4. Heartbeat emit mỗi 15–30s khi idle

---

## 7. Definition of done — step 04

- [ ] Event schema compile + export all types
- [ ] Acquire lock → 409 on second concurrent stream
- [ ] Heartbeat refresh → lock không expire trong stream dài
- [ ] Release lock trong finally — lock cleared sau stream
- [ ] Client disconnect → LLM continues, messages persisted

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [09-api-layer.md](./09-api-layer.md) | `POST /stream` wire EventBus → SSE |
| [05-orchestration-system.md](./05-orchestration-system.md) | Main loop yields events |
| [`UI/02-ui-features-chat-agent.md`](../../UI/02-ui-features-chat-agent.md) | FE SSE consumer |
