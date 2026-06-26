# 02 — ⑥ LLM System

> Lớp trừu tượng mỏng giữa agent runtime và AI providers — thay provider không chạm Orchestration.
>
> **Nguồn:** [`00-master-agent-plan.md`](../00-master-agent-plan.md) §4.2 | [`01-project-structure-and-techstack.md`](../01-project-structure-and-techstack.md) §6.6

**Location:** `packages/core/src/core/llm/`  
**Phụ thuộc:** [01-infra-and-monorepo.md](./01-infra-and-monorepo.md)

---

## 1. Mục tiêu

- [ ] 1. `LLMClient` Protocol — `chat()` + `stream()` async generator
- [ ] 2. Ollama provider (dev default, zero-cost)
- [ ] 3. Anthropic provider (production primary)
- [ ] 4. OpenAI provider (fallback alternative)
- [ ] 5. `budget.py` export constants + `GET /v1/llm/budget`

---

## 2. LLMClient Protocol

**File:** `packages/core/src/core/llm/client.py`

### 2.1 Interface

Định nghĩa `LLMClient` là **Protocol** (không abstract class):

| Method | Signature | Dùng cho |
|--------|-----------|----------|
| `chat()` | non-streaming | Title generation, compaction (Phase 2) |
| `stream()` | async generator | Main loop, agent loop |

### 2.2 Stream chunk types

`stream()` emit các chunk types:

| Chunk | Mô tả |
|-------|-------|
| `text_delta` | Text streaming từ model |
| `thinking_delta` | Extended thinking (Anthropic only) |
| `tool_call` | Tool use request (name + args + call_id) |
| `done` | Stream kết thúc + usage metadata |
| `error` | Provider error |

### 2.3 Checklist Protocol

- [ ] 1. `LLMMessage`, `LLMDelta`, `LLMResponse` Pydantic models
- [ ] 2. Orchestration import chỉ từ `core.llm` — không import provider cụ thể
- [ ] 3. Factory `get_llm_client(provider: str) -> LLMClient` đọc từ config

---

## 3. Ollama provider (dev default)

**File:** `packages/core/src/core/llm/ollama.py`

### 3.1 Implementation

- [ ] 1. `httpx.AsyncClient` gọi Ollama REST API
- [ ] 2. Endpoint: `POST /api/chat` với `stream: true`
- [ ] 3. Parse từng JSON line từ response stream
- [ ] 4. Map Ollama tool_calls format → `LLMDelta.tool_call`
- [ ] 5. Emit `text_delta` cho content chunks
- [ ] 6. **Không** emit `thinking_delta` — Ollama không hỗ trợ extended thinking

### 3.2 Dev workflow

- [ ] 1. `OLLAMA_BASE_URL` default `http://localhost:11434`
- [ ] 2. Model default configurable qua `OLLAMA_MODEL`
- [ ] 3. Test: `stream()` với simple prompt trả text delta

---

## 4. Anthropic provider (production)

**File:** `packages/core/src/core/llm/anthropic.py`

### 4.1 Implementation

- [ ] 1. Anthropic Messages API `POST /v1/messages` streaming
- [ ] 2. Handle tool use content blocks (format khác OpenAI)
- [ ] 3. Handle extended thinking blocks: signature + text + redacted
- [ ] 4. Track `usage.prompt_tokens` — exact count cho token calibration (Phase 2)
- [ ] 5. Emit `thinking_delta` khi có thinking blocks

### 4.2 Production notes

- Primary production provider
- Prefix caching friendly — history prefix stable (Phase 2 context block)

---

## 5. OpenAI provider (alternative)

**File:** `packages/core/src/core/llm/openai.py`

### 5.1 Implementation

- [ ] 1. OpenAI Chat Completions API streaming
- [ ] 2. Tool calls trong delta format OpenAI
- [ ] 3. **Không** fake extended thinking — skip `thinking_delta`
- [ ] 4. Fallback khi không dùng Anthropic

---

## 6. Token budget constants

**File:** `packages/core/src/core/llm/budget.py`

Export tất cả số liên quan token budget — FE dùng render context donut.

### 6.1 Constants (từ master plan §3.3)

| Export key | Value | Source constant |
|------------|-------|-----------------|
| `contextWindow` | 128,000 | `LLM_CONTEXT_WINDOW` |
| `inputBudgetTokens` | derived | context window minus output reserve |
| `microCompactFraction` | 0.60 | `MICRO_COMPACT_FRACTION` |
| `summaryCompactFraction` | 0.80 | `SUMMARY_COMPACT_FRACTION` |
| `keepTokens` | 40,000 | `KEEP_TOKENS` |
| `initialTokensPerChar` | 0.34 | `INITIAL_TOKENS_PER_CHAR` |
| `imageCharEquiv` | 6,000 | `IMAGE_CHAR_EQUIV` |

### 6.2 Checklist budget

- [ ] 1. Single source — `budget.py` re-export hoặc mirror `orchestration/constants.py`
- [ ] 2. Không duplicate values ở FE
- [ ] 3. `GET /v1/llm/budget` trả JSON object (wire ở [09-api-layer.md](./09-api-layer.md))

---

## 7. Provider selection

**File:** `packages/core/src/core/llm/factory.py`

- [ ] 1. Đọc `LLM_PROVIDER` env: `ollama` | `anthropic` | `openai`
- [ ] 2. Validate API key tồn tại cho cloud providers
- [ ] 3. Fail fast với message rõ nếu misconfigured
- [ ] 4. Title generation dùng cheap model config riêng (optional override)

---

## 8. Error handling (Phase 1 basic)

- [ ] 1. Provider timeout → emit `error` chunk, không crash process
- [ ] 2. HTTP 4xx/5xx → wrap thành user-friendly message
- [ ] 3. Retry logic đầy đủ (recovery paths) → defer Phase 2

---

## 9. Definition of done — step 02

- [ ] Ollama `stream()` trả `text_delta` + `done` với local model
- [ ] Anthropic hoặc OpenAI provider compile + unit test mock
- [ ] `GET /v1/llm/budget` trả keys: `contextWindow`, `inputBudgetTokens`, `microCompactFraction`, `summaryCompactFraction`
- [ ] Orchestration có thể gọi `client.stream(messages, tools)` mà không biết provider

---

## 9. Cross-references

| File | Liên quan |
|------|-----------|
| [05-orchestration-system.md](./05-orchestration-system.md) | Main loop gọi LLM stream |
| [00-prerequisites-and-scope.md](./00-prerequisites-and-scope.md) | Constants §4 |
| `research/02-leadzen` | Token accounting patterns |
