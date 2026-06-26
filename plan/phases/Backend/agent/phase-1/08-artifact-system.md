# 08 — ⑧ Artifact System (Phase 1 Basic)

> Stage file writes trong memory — flush DB chỉ khi stream thành công hoặc stop có chủ ý. Không phantom files.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.8 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.8

**Location:**  
- `packages/agents/src/agents/artifacts/buffer.py`  
- `packages/agents/src/agents/artifacts/file_service.py` (hoặc delegate `packages/db` service)

**Phụ thuộc:** [03-persistence-system.md](./03-persistence-system.md)

---

## 1. Mục tiêu

- [ ] 1. `ArtifactBuffer` — in-memory stage dict
- [ ] 2. `upsert_workspace_file()` — overwrite-by-name application logic
- [ ] 3. Flush on `stream_done` / stop handshake
- [ ] 4. Không file trong DB khi user cancel giữa chừng (trừ stop flush partial)

---

## 2. ArtifactBuffer

**File:** `packages/agents/src/agents/artifacts/buffer.py`

### 2.1 Data structure

```python
# Conceptual — keyed by file name
{
  "spec.md": { "id": UUID, "content": "..." },
  "memory.md": { "id": UUID, "content": "..." }
}
```

### 2.2 API

| Method | Mô tả |
|--------|-------|
| `stage(name, id, content)` | Stage hoặc overwrite entry trong buffer |
| `get(name)` | Get staged content — main loop đọc memory.md fresh |
| `has(name)` | Check existence |
| `keys()` | List staged file names |
| `flush(db, task_id)` | Persist all entries → DB, clear buffer |
| `clear()` | Drop without persist (error abort) |

### 2.3 Lifecycle

1. [ ] Route tạo `ArtifactBuffer()` fresh đầu mỗi stream
2. [ ] Pass shared instance vào `RuntimeContext`
3. [ ] `write_file` tool → `buffer.stage()` — không touch DB
4. [ ] Main loop kết thúc → `buffer.flush()`
5. [ ] Route `finally`: flush nếu chưa flush (safety net)
6. [ ] Hard error abort (không stop handshake) → `clear()` — no phantom files

### 2.4 Checklist buffer

- [ ] 1. Thread-safe trong single asyncio task (no lock needed Phase 1)
- [ ] 2. `get("memory.md")` ưu tiên buffer over DB (staged wins)
- [ ] 3. UUID `id` per stage — stable across overwrites same name

---

## 3. File service

**File:** `packages/agents/src/agents/artifacts/file_service.py`

Hoặc wrap `packages/db/src/db/services/file_service.py` — một implementation duy nhất.

### 3.1 upsert_workspace_file()

```
upsert_workspace_file(db, task_id, name, content, message_id?, ...)
```

Logic:

- [ ] 1. Query file by `(task_id, name)` — latest hoặc any match
- [ ] 2. Exists → UPDATE content, size, metadata
- [ ] 3. Not exists → INSERT new File record
- [ ] 4. **Không** dùng DB `ON CONFLICT` unique — app-layer overwrite
- [ ] 5. `source = workspace`, `kind = text` cho .md files

### 3.2 get_artifacts()

- [ ] Trả danh sách workspace files của task
- [ ] Include `name`, `content`, `size`, `kind`, `created_at`

### 3.3 get_file()

- [ ] Lookup single file by `(task_id, name)`
- [ ] Check buffer first if active run (via ctx)

---

## 4. file_artifact SSE event

Khi `write_file` stages:

- [ ] 1. Emit ngay `file_artifact` với `name`, `content`, `kind`
- [ ] 2. FE preview trước khi flush DB
- [ ] 3. Sau flush, `GET /artifacts` consistent với streamed content

---

## 5. Ownership remap (Phase 1 basic)

Phase 2 thêm `flush_and_remap()` đầy đủ. Phase 1:

- [ ] 1. On flush: set `message_id` = final assistant message của turn
- [ ] 2. Files linked đúng message cho UI canvas

---

## 6. Phantom file prevention

| Scenario | Expected behavior |
|----------|-------------------|
| Stream success | All staged files → DB |
| `POST /stop` | Flush staged files (partial work kept) |
| Client disconnect | Continue run → flush on done |
| Uncaught exception mid-stream | **No flush** — buffer cleared |
| User cancel before any write | No files in DB |

- [ ] 1. Test: interrupt before write → `GET /artifacts` empty of new files
- [ ] 2. Test: stop during write → spec.md persisted

---

## 7. Integration points

| Caller | Action |
|--------|--------|
| `write_file` tool | `buffer.stage()` + emit SSE |
| `main_loop` step 5 | `buffer.flush()` |
| `main_loop` iteration | `buffer.get("memory.md")` refresh |
| `list_file` tool | merge DB + buffer keys |
| `read_file` tool | buffer first, then DB |
| Stream route `finally` | safety flush or clear |

---

## 8. Definition of done — step 08

- [ ] `write_file` không ghi DB trực tiếp
- [ ] `stream_done` → `spec.md` trong DB với content đúng
- [ ] `GET /artifacts` trả spec.md sau successful stream
- [ ] Cancel mid-stream (exception) → no phantom spec.md
- [ ] `POST /stop` → partial spec.md flushed if staged

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [07-tool-system.md](./07-tool-system.md) | write_file implementation |
| [05-orchestration-system.md](./05-orchestration-system.md) | Flush on turn end |
| Master plan §5.7 | Production buffer remap Phase 2 |
