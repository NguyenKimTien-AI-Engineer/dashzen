# 10 — Checklist & Definition of Done

> Checklist cuối Phase 1 — **phải PASS toàn bộ** trước khi bắt đầu Phase 2. Không có ngoại lệ.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.10

---

## 1. Definition of Done (13 items)

Copy đầy đủ từ master plan:

- [ ] **1.** `docker compose up` → cả 3 services (postgres, redis, minio) healthy, không crash sau 30 giây
- [ ] **2.** `POST /v1/auth/login` với credentials hợp lệ → nhận JWT cookie; gọi protected endpoint không có cookie → 401
- [ ] **3.** `POST /v1/tasks` → task được tạo trong DB với `status=active`, `type=null`, `title=null`; workspace file `memory.md` được tạo với `type: chat`
- [ ] **4.** `POST /v1/tasks/{id}/stream` với user message → nhận SSE events bao gồm ít nhất một `main_text` event
- [ ] **5.** Main loop gọi `spawn_agent("dashboard-planner")` → nhận sequence `agent_start` → một hoặc nhiều `agent_tool`/`agent_result` → `agent_done` với status `"done"`
- [ ] **6.** Dashboard planner gọi `write_file("spec.md")` → nhận `file_artifact` event với `name="spec.md"` và content
- [ ] **7.** Sau khi stream kết thúc, `GET /v1/tasks/{id}/messages` → trả message list bao gồm cả user message và assistant message; agent activities visible trong response
- [ ] **8.** `GET /v1/tasks/{id}/artifacts` → trả danh sách files bao gồm `spec.md` với content đúng
- [ ] **9.** `POST /v1/tasks/{id}/stop` trong khi stream đang chạy → stream dừng lại, `stream_done` được emit, lock được release
- [ ] **10.** Gửi `POST /v1/tasks/{id}/stream` khi task đang stream → nhận **409** `"Task is already being processed"`
- [ ] **11.** Đóng browser/ngắt kết nối client khi stream đang chạy → LLM **KHÔNG** bị cancel; khi reconnect vẫn thấy message được persist đầy đủ
- [ ] **12.** `GET /v1/llm/budget` → trả JSON object với các keys: `contextWindow`, `inputBudgetTokens`, `microCompactFraction`, `summaryCompactFraction`
- [ ] **13.** Sau turn 1, task có title được set (có thể cần turn 8 với `TITLE_FORCE_BY_TURN`)

---

## 2. Per-step verification map

| DoD # | Step plan | Subsystem |
|-------|-----------|-----------|
| 1 | [01-infra-and-monorepo.md](./01-infra-and-monorepo.md) | Docker |
| 2 | [09-api-layer.md](./09-api-layer.md) + [`auth/`](../auth/) | Auth |
| 3 | [03-persistence-system.md](./03-persistence-system.md) | Persistence |
| 4 | [04](./04-streaming-system.md) + [05](./05-orchestration-system.md) + [09](./09-api-layer.md) | Stream |
| 5 | [05](./05-orchestration-system.md) + [06](./06-agent-registry.md) | Orchestration + Registry |
| 6 | [07](./07-tool-system.md) + [08](./08-artifact-system.md) | Tools + Artifact |
| 7 | [03](./03-persistence-system.md) + [05](./05-orchestration-system.md) | Messages + AgentRun |
| 8 | [08](./08-artifact-system.md) | Artifact flush |
| 9 | [04](./04-streaming-system.md) + [09](./09-api-layer.md) | Stop handshake |
| 10 | [04](./04-streaming-system.md) | Stream lock |
| 11 | [04](./04-streaming-system.md) | Disconnect resilience |
| 12 | [02-llm-system.md](./02-llm-system.md) | Budget API |
| 13 | [05-orchestration-system.md](./05-orchestration-system.md) | Auto-title |

---

## 3. Test cases chi tiết

### 3.1 Infra (DoD #1)

```bash
docker compose -f infra/compose/docker-compose.yml up -d
docker compose ps  # all healthy
sleep 30
docker compose ps  # still running
```

### 3.2 Auth (DoD #2)

```bash
# With credentials → 200 + Set-Cookie
curl -v -X POST /v1/auth/login -d '...'

# Without cookie → 401
curl -v GET /v1/tasks
```

### 3.3 Task create (DoD #3)

```bash
curl -b cookies -X POST /v1/tasks
# Verify DB: tasks row + files row memory.md
```

### 3.4 Happy path stream (DoD #4–8)

**Input:** `"tạo dashboard doanh thu"`

**Expected SSE sequence (subset):**
```
main_text (orchestrator acknowledges)
main_tool (spawn_agent)
agent_start (dashboard-planner)
agent_tool (write_file)
agent_result
file_artifact (spec.md)
agent_done (status: done)
stream_done
```

**Post-stream:**
- `GET /messages` → user + assistant messages
- `GET /artifacts` → spec.md with dashboard spec content

### 3.5 Stop handshake (DoD #9)

1. Start long-running stream
2. `POST /stop` while streaming
3. Verify: `stream_done` received, lock released, partial content persisted

### 3.6 Concurrent stream (DoD #10)

1. Start stream (don't wait for done)
2. Second `POST /stream` → 409

### 3.7 Disconnect resilience (DoD #11)

1. Start stream
2. Kill curl client (`Ctrl+C`) mid-stream
3. Wait for server to complete
4. `GET /messages` → full assistant response present

### 3.8 Budget API (DoD #12)

```bash
curl /v1/llm/budget | jq 'keys'
# Must include: contextWindow, inputBudgetTokens, microCompactFraction, summaryCompactFraction
```

### 3.9 Auto-title (DoD #13)

1. Create task, send one message, wait stream done
2. `GET /tasks/{id}` → `title` not null (or send 8 turns for force)

---

## 4. Negative test cases

| Case | Expected |
|------|----------|
| Stream task of another user | 403 |
| `spawn_agent("nonexistent")` | Error in tool result, stream continues or errors gracefully |
| `read_file("../etc/passwd")` | Error message, no file read |
| LLM provider down | `stream_error` event, lock released |
| Redis down (dev) | In-memory lock fallback works |

---

## 5. File map Phase 1 → Code

Từ master plan §10 — files cần tồn tại sau Phase 1:

### packages/agents/

| File | Step |
|------|------|
| `orchestration/constants.py` | 05 |
| `orchestration/runtime.py` | 05 |
| `orchestration/main_loop.py` | 05 |
| `orchestration/agent_loop.py` | 05 |
| `orchestration/spawn.py` | 05 |
| `orchestration/task_title.py` | 05 |
| `orchestration/exec_parallel.py` | 05 |
| `registry/schema.py` | 06 |
| `registry/loader.py` | 06 |
| `registry/cache.py` | 06 |
| `tools/registry.py` | 07 |
| `tools/loop_detection.py` | 07 |
| `tools/read_cache.py` | 07 |
| `tools/partition.py` | 07 |
| `artifacts/buffer.py` | 08 |
| `artifacts/file_service.py` | 08 |
| `streaming/events.py` | 04 |
| `streaming/event_bus.py` | 04 |
| `streaming/lock.py` | 04 |
| `streaming/guards.py` | 04 |

### packages/tools/

| File | Step |
|------|------|
| `file/read_file.py` | 07 |
| `file/write_file.py` | 07 |
| `file/list_file.py` | 07 |
| `orchestration/spawn_agent.py` | 07 |

### packages/core/

| File | Step |
|------|------|
| `llm/client.py` | 02 |
| `llm/ollama.py` | 02 |
| `llm/anthropic.py` | 02 |
| `llm/openai.py` | 02 |
| `llm/budget.py` | 02 |
| `llm/factory.py` | 02 |

### packages/agents/prompts/

| File | Step |
|------|------|
| `system/system-main.md` | 06 |
| `system/system-agent.md` | 06 |
| `agents/dashboard-planner.md` | 06 |

### apps/api/

| File | Step |
|------|------|
| `routes/tasks.py` | 09 |
| `routes/stream.py` | 09 |
| `routes/llm.py` | 09 |

---

## 6. Gate sang Phase 2

Phase 2 **không bắt đầu** until:

- [ ] Tất cả 13 DoD items PASS
- [ ] Code review: dependency direction đúng
- [ ] Không phantom files trên cancel test
- [ ] Document any known limitations trong implementation notes

**Phase 2 adds:** Memory FSM, 4 more agents, HITL gates, compaction, full tool pipeline, rate limits, upload.

---

## 7. Implementation order (tóm tắt)

```
00 Read scope
01 Infra
02 LLM
03 Persistence
04 Streaming
08 Artifact (before write_file)
07 Tools
06 Registry + prompts
05 Orchestration (largest)
09 API wire
10 E2E checklist
```

---

## 8. Cross-references

| File | Liên quan |
|------|-----------|
| [README.md](./README.md) | Phase 1 overview |
| [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5 | Phase 2 scope |
| [`research/03-comparison-synthesis.md`](../../../research/03-comparison-synthesis.md) | LeadZen file mapping |
