# 04 — ④ Tool System — Full Execution Pipeline

> Mọi tool call qua pipeline 6 bước cố định + bổ sung tool implementations Phase 2.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.4

**Location:**  
- `packages/agents/src/agents/tools/pipeline.py`  
- `packages/tools/src/tools/`

**Phụ thuộc:** [Phase 1 07-tool-system](../phase-1/07-tool-system.md), [06-gate-system-hitl](./06-gate-system-hitl.md)

---

## 1. Mục tiêu

- [ ] 1. `pipeline.py` — 6-step execution pipeline
- [ ] 2. `edit_file.py` — patch portion of file
- [ ] 3. `set_memory.py` — (see [01-memory-system.md](./01-memory-system.md))
- [ ] 4. `ask_user.py` — ask gate integration
- [ ] 5. `schema_inspector.py` — mock schema Phase 2
- [ ] 6. `csv_preview.py` — parse CSV upload
- [ ] 7. Update registry tiers — new tools in correct sets

---

## 2. Full tool execution pipeline

**File:** `packages/agents/src/agents/tools/pipeline.py`

Thay thế Phase 1 direct execution. **Thứ tự cố định — không đổi:**

### Bước 1 — Validate args

- [ ] Parse tool arguments theo JSON Schema (`parameters` per tool)
- [ ] Args invalid → return error envelope ngay, **không execute**

### Bước 2 — Loop detection

- [ ] Check `LoopDetector`
- [ ] Warn level (≥3) → inject warning vào result, **vẫn execute**
- [ ] Block level (≥5) → return block error, **không execute**

### Bước 3 — Read cache dedup

- [ ] Tool là `READ_ONLY` + cache hit `(tool_name, args)` → cached result
- [ ] Không execute

### Bước 4 — Gate (ask mode)

- [ ] `mode=ask` AND tool **không** trong `ASK_BYPASS`:
  - `init_gate()` **TRƯỚC** emit SSE
  - Emit `main_tool` event
  - Block poll user decision
  - Rejected → return `TOOL_REJECTED_RESULT` sentinel
  - Approved → tiếp tục
- [ ] `mode=auto` → skip step

### Bước 5 — Execute

- [ ] `tool.execute(args, tool_ctx)`
- [ ] try/except → mọi exception → error envelope, **không crash stream**

### Bước 6 — Truncate result

- [ ] Cap theo `TOOL_RESULT_MAX_CHARS` (per-tool)
- [ ] Cap theo `HISTORY_CAP_CHARS` (history total)
- [ ] Tránh context overflow turns sau

### Pipeline API

```python
# Conceptual
async def execute_tool(tool_call, ctx) -> ToolResult:
    # steps 1-6 in order
```

- [ ] 1. `exec_parallel.py` gọi pipeline thay vì direct execute
- [ ] 2. Agent loop cũng qua pipeline

---

## 3. Tool registry updates

**File:** `packages/agents/src/agents/tools/registry.py`

### 3.1 New tools tier assignment

| Tool | READ_ONLY | ASK_BYPASS | VISIBLE | CONCURRENT_SAFE | MAIN | AGENT |
|------|-----------|------------|---------|-----------------|------|-------|
| `edit_file` | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| `set_memory` | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| `ask_user` | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `schema_inspector` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `csv_preview` | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |

- [ ] 1. `spawn_agent` remains MAIN only
- [ ] 2. `set_memory` MAIN only — FSM main loop control
- [ ] 3. `ask_user` MAIN only — headless sub-agents

---

## 4. edit_file

**File:** `packages/tools/src/tools/file/edit_file.py`

- [ ] 1. Patch portion của file workspace — không overwrite toàn bộ
- [ ] 2. Hữu ích: sửa một widget trong `page.tsx` không rebuild
- [ ] 3. Stage vào ArtifactBuffer (giống write_file)
- [ ] 4. Emit `file_artifact` SSE
- [ ] 5. Invalidate ReadCache cho path
- [ ] 6. Path traversal prevention

**Parameters JSON Schema:**

```json
{
  "path": "string",
  "old_string": "string",
  "new_string": "string"
}
```

---

## 5. ask_user

**File:** `packages/tools/src/tools/orchestration/ask_user.py`

- [ ] 1. Trigger ask gate — namespace `ask:{task_id}:{call_id}`
- [ ] 2. Emit `main_ask` SSE với câu hỏi
- [ ] 3. Block đợi user submit qua `POST /gates/ask`
- [ ] 4. Trả answer về LLM như tool result
- [ ] 5. Trong `ASK_BYPASS` — không Y/N approval card (bản thân là interaction)

---

## 6. schema_inspector

**File:** `packages/tools/src/tools/data/schema_inspector.py`

**Phase 2:** mock schema hardcoded trong tool/prompt.

- [ ] 1. Trả mock data source schema (tables, columns, types)
- [ ] 2. data-binder dùng để grounded generation
- [ ] 3. Phase 3+ thay bằng real DB introspection
- [ ] 4. READ_ONLY + CONCURRENT_SAFE

---

## 7. csv_preview

**File:** `packages/tools/src/tools/data/csv_preview.py`

- [ ] 1. Parse CSV file từ upload (`source: upload`)
- [ ] 2. Infer schema (column names, types)
- [ ] 3. Trả preview data (rows capped)
- [ ] 4. READ_ONLY + CONCURRENT_SAFE

---

## 8. set_memory

Đã mô tả đầy đủ tại [01-memory-system.md](./01-memory-system.md) §5.

- [ ] Wire vào pipeline step 5 execute
- [ ] Trong `ASK_BYPASS` — skip gate step 4

---

## 9. Per-tool JSON Schema

Mỗi tool export:

```python
{
  "name": "tool_name",
  "description": "...",
  "parameters": { /* JSON Schema */ }
}
```

- [ ] 1. Tất cả tools có `parameters` schema
- [ ] 2. Pipeline step 1 validates against schema
- [ ] 3. Schemas exposed to LLM provider tool definitions

---

## 10. Definition of done — step 04

- [ ] All tool calls go through 6-step pipeline
- [ ] Ask mode: write_file shows gate, approve continues
- [ ] `ask_user` emits main_ask, blocks until answer
- [ ] `edit_file` patches page.tsx portion
- [ ] `schema_inspector` returns mock schema
- [ ] `csv_preview` works on uploaded CSV
- [ ] Invalid args rejected at step 1

---

## 11. Cross-references

| File | Liên quan |
|------|-----------|
| [06-gate-system-hitl.md](./06-gate-system-hitl.md) | Step 4 gate |
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | exec_parallel uses pipeline |
| [07-artifact-and-upload.md](./07-artifact-and-upload.md) | Upload files for csv_preview |
