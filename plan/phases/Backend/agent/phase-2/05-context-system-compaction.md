# 05 — ⑤ Context System — Full Compaction

> History builder, 2-tier compaction, token accounting calibration, thinking codec, manual compact API.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §5.5

**Location:** `packages/agents/src/agents/context/`  
**Phụ thuộc:** [Phase 1 02-llm-system](../phase-1/02-llm-system.md), [09-persistence-branching](./09-persistence-branching.md)

---

## 1. Mục tiêu

- [ ] 1. `history.py` — build_history + compact summary message
- [ ] 2. `compaction.py` — compact_if_over_budget() 2-tier
- [ ] 3. `accounting.py` — estimate_chars + calibrate_tokens_per_char
- [ ] 4. `thinking_codec.py` — encode/decode thinking blocks
- [ ] 5. Wire vào main_loop mỗi iteration
- [ ] 6. `POST /v1/tasks/{id}/compact` API ([10-api-layer-extensions](./10-api-layer-extensions.md))

---

## 2. History builder

**File:** `packages/agents/src/agents/context/history.py`

### 2.1 build_history(path)

Input: messages theo tree path (root → leaf).

Output: `list[LLMMessage]` đúng format provider.

| Role | Conversion |
|------|------------|
| user | text content |
| assistant + tool_calls | tool_calls format |
| tool | role=tool content |
| compact | **Đặc biệt** — không hiện trong history, chỉ boundary marker |

### 2.2 build_compact_summary_message(summary)

- [ ] 1. Tạo user message với nội dung summary
- [ ] 2. **Prepend** đầu list — "leading user message" (Claude layout)
- [ ] 3. Model đọc summary trước recent history
- [ ] 4. **Không** inject vào context block

### 2.3 Thinking reconstruction

- [ ] Messages có `thinking` column → decode qua thinking_codec
- [ ] Reconstruct đúng format provider khi resend

---

## 3. Two-tier compaction

**File:** `packages/agents/src/agents/context/compaction.py`

### 3.1 compact_if_over_budget()

Gọi **đầu mỗi iteration** main loop.

### 3.2 Token estimation

```
currentInputTokens = lastRealPromptTokens
                   + estimated_delta(messages_since_last_call)
```

- [ ] `lastRealPromptTokens` — exact từ provider call gần nhất
- [ ] Delta dùng calibrated `tokensPerChar` ratio

### 3.3 Thresholds (từ §3.3 constants)

| Threshold | Value | Action |
|-----------|-------|--------|
| `microAtTokens` | 60% budget (`MICRO_COMPACT_FRACTION`) | Tier 1 |
| `compactAtTokens` | 80% budget (`SUMMARY_COMPACT_FRACTION`) | Tier 2 |
| `KEEP_TOKENS` | 40,000 | Keep recent history |

### 3.4 Tier 1 — Microcompact

- [ ] Scan messages array in-memory
- [ ] Xóa content old tool result messages (role=tool, nửa đầu history)
- [ ] Giữ placeholder
- [ ] **Không cần LLM** — cheap, 20–40% token savings
- [ ] Trigger khi > 60% budget

### 3.5 Tier 2 — Summary compact

Chỉ khi sau tier 1 vẫn > 80% budget:

1. [ ] Reload full message path từ DB
2. [ ] Xác định split point — keep `KEEP_TOKENS` (40k) gần nhất
3. [ ] Gọi **cheap LLM model** summarize phần cũ
4. [ ] Persist summary message — `role=compact` vào DB
5. [ ] Rebuild messages: kept tail + summary prepended (leading user message)

### 3.6 compactionExhausted flag

- [ ] Sau compact, kept tail vẫn > budget → set flag
- [ ] Không compact thêm trong turn này (tránh thrashing)

---

## 4. Token accounting calibration

**File:** `packages/agents/src/agents/context/accounting.py`

### 4.1 estimate_chars(messages)

- [ ] Tổng chars: text content + tool call JSON + thinking

### 4.2 calibrate_tokens_per_char(real_prompt_tokens, messages)

```
ratio = real_prompt_tokens / estimated_chars_at_send
```

- [ ] 1. Sau mỗi LLM call thực tế — recalibrate ratio
- [ ] 2. Ratio mới dùng cho delta estimation messages thêm sau
- [ ] 3. Init: `INITIAL_TOKENS_PER_CHAR = 0.34` (Vietnamese conservative)

### 4.3 Wire vào main_loop

- [ ] Sau mỗi LLM stream done → calibrate từ usage metadata
- [ ] Store `lastRealPromptTokens` in iteration state

---

## 5. Thinking codec

**File:** `packages/agents/src/agents/context/thinking_codec.py`

Extended thinking blocks: text + signature + redacted.

| Function | Mô tả |
|----------|-------|
| `encode_thinking(blocks)` | Structured → JSON string cho `Message.thinking` |
| `decode_thinking(json_str)` | JSON string → structured for provider resend |

- [ ] 1. Round-trip lossless cho Anthropic thinking blocks
- [ ] 2. Load history reconstructs thinking in LLM payload

---

## 6. Manual compact API

**Endpoint:** `POST /v1/tasks/{id}/compact` — xem [10-api-layer-extensions.md](./10-api-layer-extensions.md)

- [ ] 1. User trigger summary compact bất kỳ lúc nào
- [ ] 2. Không cần đợi 80% threshold
- [ ] 3. Response trả summary được tạo
- [ ] 4. Useful: "reset" conversation dài

---

## 7. main_loop integration

Mỗi iteration, **trước** LLM call:

```
1. compact_if_over_budget(messages, state)
2. build_history(path) → LLM messages prefix
3. build_context_block() → append (NOT in messages array)
4. LLM stream
5. calibrate_tokens_per_char(usage.prompt_tokens)
```

- [ ] 1. Context block separate from history prefix (cache-friendly)
- [ ] 2. Compact boundary messages hidden in UI ([09](./09-persistence-branching.md))

---

## 8. Definition of done — step 05

- [ ] Long conversation triggers microcompact at 60%
- [ ] Summary compact at 80% persists role=compact message
- [ ] `POST /compact` manual trigger works
- [ ] Token ratio calibrates after real provider usage
- [ ] Thinking blocks round-trip through DB
- [ ] Compact summary prepended as leading user message

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [03-orchestration-full-pipeline.md](./03-orchestration-full-pipeline.md) | main_loop wire |
| [09-persistence-branching.md](./09-persistence-branching.md) | compact role messages |
| `research/02-leadzen` | 2-tier compaction algorithms |
