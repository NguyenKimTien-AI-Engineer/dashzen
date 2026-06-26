# 07 — ④ Tool System (Phase 1 Basic)

> Tool registry tiers, loop detection, read cache, batch partitioning, và 3 file tools.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.7 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.4

**Location:**  
- Registry/tiers: `packages/agents/src/agents/tools/`  
- Implementations: `packages/tools/src/tools/file/`

**Phụ thuộc:** [08-artifact-system.md](./08-artifact-system.md) (write_file stages buffer)

---

## 1. Mục tiêu

- [ ] 1. Tool registry 6 tiers — single source of truth
- [ ] 2. `LoopDetector` — warn@3, block@5
- [ ] 3. `ReadCache` — per-run dedup
- [ ] 4. `partition_batches()` — concurrent vs serial
- [ ] 5. Implement: `read_file`, `write_file`, `list_file`
- [ ] 6. `spawn_agent` tool wrapper (delegate → spawn.py)

---

## 2. Tool registry tiers

**File:** `packages/agents/src/agents/tools/registry.py`

### 2.1 Six tiers

| Tier | Members Phase 1 | Mục đích |
|------|-----------------|----------|
| `READ_ONLY_TOOLS` | `read_file`, `list_file` | Bypass gate (Phase 2) |
| `ASK_BYPASS` | READ_ONLY + `spawn_agent` | Không cần Y/N card |
| `VISIBLE_TOOLS` | `write_file`, `spawn_agent` | Hiện activity row UI |
| `CONCURRENT_SAFE` | READ_ONLY tools | Chạy song song |
| `MAIN_TOOLS` | `spawn_agent`, `read_file`, `write_file`, `list_file` | Main loop full set |
| `AGENT_TOOLS` | `read_file`, `write_file`, `list_file` | Sub-agent — **không** spawn_agent |

### 2.2 Phase 1 exclusions (by design)

| Tool | Lý do không có Phase 1 |
|------|------------------------|
| `set_memory` | Memory FSM → Phase 2 |
| `ask_user` | HITL → Phase 2 |
| `edit_file` | Phase 2 |
| `schema_inspector` | Phase 2 |

### Checklist registry

- [ ] 1. `is_read_only(tool_name) -> bool`
- [ ] 2. `is_concurrent_safe(tool_name) -> bool`
- [ ] 3. `get_main_tools() -> list`
- [ ] 4. `get_agent_tools() -> list`
- [ ] 5. `resolve_agent_tools(definition) -> list` — apply allowlist/disallowlist

---

## 3. Loop detection

**File:** `packages/agents/src/agents/tools/loop_detection.py`

### 3.1 LoopDetector class

- [ ] Track history tool calls trong sliding window
- [ ] Key = `(tool_name, args_json_sorted)`
- [ ] Same call ≥ **3 lần** → **warn** (inject warning vào result, vẫn execute)
- [ ] Same call ≥ **5 lần** → **block** (error message, không execute)

### 3.2 Checklist

- [ ] 1. Sliding window — detect xen kẽ với calls khác
- [ ] 2. Reset per main loop turn (hoặc per agent run)
- [ ] 3. Warning text rõ ràng cho LLM

---

## 4. Read cache

**File:** `packages/agents/src/agents/tools/read_cache.py`

### 4.1 ReadCache class

- [ ] Key = `(tool_name, normalized_args)`
- [ ] `read_file("spec.md")` × 3 trong cùng turn → disk/DB read lần 1, cache lần 2–3
- [ ] Invalidate khi `write_file` hoặc `edit_file` cùng path

### 4.2 Lifecycle

- [ ] 1. Tạo fresh mỗi `run_task()` / agent run
- [ ] 2. Không share giữa tasks

---

## 5. Batch partitioning

**File:** `packages/agents/src/agents/tools/partition.py`

### 5.1 partition_batches()

Thuật toán linear scan:

- [ ] Call hiện tại `CONCURRENT_SAFE` AND batch cuối cũng `CONCURRENT_SAFE` → merge batch
- [ ] Ngược lại → tạo batch serial mới
- [ ] Kết quả: `list[list[ToolCall]]`

### 5.2 Invariant

- Read-only calls nhóm parallel
- Write/spawn calls luôn serial
- Single source cho main loop và agent loop

---

## 6. Tool implementations

### 6.1 read_file

**File:** `packages/tools/src/tools/file/read_file.py`

| Step | Mô tả |
|------|-------|
| Validate | Path không chứa `../` traversal |
| Lookup | File model `(task_id, name)` |
| Miss | Error message rõ — không throw uncaught exception |
| Hit | Return content string |
| Cache | Check ReadCache trước khi DB read |

- [ ] 1. JSON Schema parameters: `{ "path": string }`
- [ ] 2. Tool descriptor export cho LLM

### 6.2 write_file

**File:** `packages/tools/src/tools/file/write_file.py`

| Step | Mô tả |
|------|-------|
| Validate | Path traversal check |
| Stage | `ArtifactBuffer.stage(name, id, content)` — **không** ghi DB ngay |
| Emit | `file_artifact` SSE event ngay (FE preview) |
| Invalidate | ReadCache cho path đó |

- [ ] 1. Parameters: `{ "path": string, "content": string }`
- [ ] 2. Emit event qua `ctx.event_emit`
- [ ] 3. Return success message cho LLM

### 6.3 list_file

**File:** `packages/tools/src/tools/file/list_file.py`

| Step | Mô tả |
|------|-------|
| Query | All files workspace của task |
| Return | `name`, `size`, `kind`, `created_at` — **không** content |

- [ ] 1. Include staged files từ ArtifactBuffer (chưa flush)
- [ ] 2. Merge DB files + buffer entries

### 6.4 spawn_agent

**File:** `packages/tools/src/tools/orchestration/spawn_agent.py`

- [ ] 1. Parameters: `{ "agent": string, "task": string }`
- [ ] 2. Delegate to `spawn.py` orchestration module
- [ ] 3. Return compact result (Status/Summary or full if ≤ 4k)
- [ ] 4. Trong `MAIN_TOOLS` only — không trong `AGENT_TOOLS`

---

## 7. Tool context (ToolCtx)

Shared context passed to every tool execute:

| Field | Mô tả |
|-------|-------|
| `task_id` | |
| `user_id` | |
| `db` | AsyncSession |
| `artifact_buffer` | ArtifactBuffer |
| `read_cache` | ReadCache |
| `event_emit` | SSE emit callback |
| `mode` | auto/ask |

- [ ] 1. `ToolCtx` dataclass trong `packages/tools` hoặc `packages/agents`
- [ ] 2. Immutable per call where possible

---

## 8. Phase 1 execution path (simplified)

Phase 2 thêm 6-step pipeline. Phase 1:

```
tool_call
  → loop_detection check
  → read_cache check (if read-only)
  → tool.execute(args, ctx)
  → return result
```

- [ ] 1. No gate step (auto mode)
- [ ] 2. Basic try/except → error envelope
- [ ] 3. No arg JSON Schema validation step (optional stub)

---

## 9. Definition of done — step 07

- [ ] `read_file` đọc `memory.md` sau task create
- [ ] `write_file("spec.md")` stages buffer + emits `file_artifact`
- [ ] `list_file` trả workspace files including staged
- [ ] `spawn_agent` delegates và returns compact output
- [ ] Loop detection blocks identical call at 5
- [ ] Read cache dedups within same turn

---

## 10. Cross-references

| File | Liên quan |
|------|-----------|
| [05-orchestration-system.md](./05-orchestration-system.md) | exec_parallel calls tools |
| [08-artifact-system.md](./08-artifact-system.md) | Buffer stage/flush |
| Master plan §5.4 | Full 6-step pipeline Phase 2 |
