# 03 — Token Usage Checklist

> **Master plan:** [`../../token-usage.md`](../../token-usage.md)
>
> **Backend detail:** [`01-token-usage-backend.md`](./01-token-usage-backend.md)
>
> **UI detail:** [`../UI/usage/02-token-usage-ui.md`](../UI/usage/02-token-usage-ui.md)

Đánh dấu `[x]` khi hoàn thành. Thứ tự bắt buộc — phase sau phụ thuộc phase trước.

---

## Phase A — Database & service

- [ ] **A1** Tạo migration `010_token_usage.py`
  - [ ] Table `llm_usage_events` + indexes
  - [ ] `users.total_input_tokens`, `users.total_output_tokens`
  - [ ] `tasks.total_input_tokens`, `tasks.total_output_tokens`
  - [ ] `messages.output_tokens`, `messages.turn_id` + index
- [ ] **A2** `alembic upgrade head` chạy thành công local
- [ ] **A3** Model `LlmUsageEvent` + export `__init__.py`
- [ ] **A4** Update `User`, `Task`, `Message` models
- [ ] **A5** Implement `usage_service.py`
  - [ ] `record_usage` — insert + bump counters
  - [ ] `get_user_usage`
  - [ ] `get_task_usage`
  - [ ] `sum_turn_usage`
  - [ ] Skip khi input=0 và output=0
  - [ ] Task update scoped by `user_id`
- [ ] **A6** Tests `test_usage_service.py` (≥ 4 cases)
- [ ] **A7** `UsageAccumulator` helper

---

## Phase B — Core LLM

- [ ] **B1** Add `LLMUsage`, `LLMChatResult` to `types.py`
- [ ] **B2** Update `LLMClient` protocol — `chat() -> LLMChatResult`
- [ ] **B3** Update provider `chat()` methods:
  - [ ] `openai.py`
  - [ ] `anthropic.py`
  - [ ] `gemini.py`
  - [ ] `openrouter.py`
  - [ ] `ollama.py`
- [ ] **B4** Fix call sites:
  - [ ] `compaction.py` — `_summarize_messages`, `manual_compact`
  - [ ] `task_title.py` — `generate_title`
- [ ] **B5** Update test mocks returning `LLMChatResult`
- [ ] **B6** `ruff` + `mypy` pass on `packages/core`

---

## Phase C — Orchestration

- [ ] **C1** `streaming/events.py`
  - [ ] `UsageUpdateEvent`
  - [ ] `StreamDoneEvent` + turn totals
  - [ ] Update `StreamEvent` union
- [ ] **C2** `activity_log.py`
  - [ ] `ActivityLog.usage_*` fields
  - [ ] `set_usage()` method
  - [ ] `to_dict()` includes `usage` when non-zero
- [ ] **C3** `tools/context.py`
  - [ ] `turn_id: UUID | None`
  - [ ] `turn_usage: UsageAccumulator | None`
- [ ] **C4** `main_loop.py`
  - [ ] Generate `turn_id` per turn
  - [ ] Capture `output_tokens` from stream done
  - [ ] `record_usage` per orchestrator iteration
  - [ ] Emit `UsageUpdateEvent`
  - [ ] `create_message` with `output_tokens`, `turn_id`
  - [ ] `activity_acc.set_usage` before final persist
  - [ ] `StreamDoneEvent` with turn totals
  - [ ] Pass `turn_id` to `ToolContext` and `try_set_title`
- [ ] **C5** `agent_loop.py`
  - [ ] Capture usage on stream done
  - [ ] `record_usage(source="sub_agent")`
  - [ ] Update shared `turn_usage` + emit `UsageUpdateEvent`
- [ ] **C6** `compaction.py`
  - [ ] Accept `user_id`, `turn_id`
  - [ ] Record compaction usage after `chat()`
- [ ] **C7** `task_title.py`
  - [ ] Accept `user_id`, `turn_id`
  - [ ] Record title usage after `chat()`
- [ ] **C8** `message_service.py`
  - [ ] `create_message` — `output_tokens`, `turn_id` params
  - [ ] `_enrich_message` — expose new fields in API dict
- [ ] **C9** Integration test: mock stream with usage → DB events exist
- [ ] **C10** Metrics `record_llm_usage` (optional)

---

## Phase D — API

- [ ] **D1** `core/schemas/auth.py` — `UsageSummary`, extend `UserResponse`
- [ ] **D2** `auth_responses.py` — populate `usage` from `get_user_usage`
- [ ] **D3** `api/schemas/tasks.py`
  - [ ] `ActivityLogUsage`
  - [ ] `MessageResponse.output_tokens`, `turn_id`
- [ ] **D4** Verify `GET /v1/tasks/{id}/messages` returns `activity_log.usage`
- [ ] **D5** `test_stream_api.py` — assert `usage_update` in SSE
- [ ] **D6** `test_auth_integration.py` or account test — `/me` includes `usage`
- [ ] **D7** API tests pass

---

## Phase E — Frontend

- [ ] **E1** Types: `activity-log.ts`, `stream-events.ts`, `task-state.ts`, `auth.ts`, `api.ts`
- [ ] **E2** `format-tokens.ts` + tests
- [ ] **E3** `map-stream-event.ts` — `usage_update`, `stream_done` totals
- [ ] **E4** `task-reducer.ts` — `USAGE_UPDATE`, `turnUsage` state
- [ ] **E5** `task-connection.tsx` — handle `usage_update` SSE
- [ ] **E6** `task-context.tsx` — invalidate `["auth","me"]` on stream end
- [ ] **E7** `useTask.ts` — expose `turnUsage`
- [ ] **E8** `ActivityBlocks.tsx` — `ThinkingPanel` usage in header
- [ ] **E9** `ChatMessageList.tsx` — wire live + persisted usage
- [ ] **E10** `AccountSettingsPanel.tsx` — lifetime usage section
- [ ] **E11** `patch-message-cache.ts` — preserve new fields
- [ ] **E12** Frontend tests pass

---

## Phase F — QA & ship

- [ ] **F1** Manual QA — live Thinking usage updates
- [ ] **F2** Manual QA — persisted usage after refresh
- [ ] **F3** Manual QA — Settings Account totals
- [ ] **F4** Manual QA — sub-agent turn increases usage
- [ ] **F5** Manual QA — stream abort retains partial usage in DB
- [ ] **F6** Manual QA — mobile layout 320px
- [ ] **F7** Full test suite green (`pytest`, `pnpm test`)
- [ ] **F8** Lint + mypy green
- [ ] **F9** Update master plan status → **Done**
- [ ] **F10** No hardcoded assistant prose in Python (agent-no-hardcode rule)

---

## Definition of Done (copy from master plan)

- [ ] Mỗi LLM call trong turn ghi `llm_usage_events`
- [ ] `users.total_*` = lifetime usage
- [ ] `tasks.total_*` = conversation usage
- [ ] SSE `usage_update` → live Thinking header
- [ ] Persisted `activity_log.usage` → historical Thinking header
- [ ] Settings Account: input / output / total
- [ ] Sub-agent + compaction + title counted
- [ ] ≥ 15 tests mới

---

## Rollback plan

1. Revert FE deploy (usage UI hidden if API fields missing — backward compatible)
2. `alembic downgrade -1` — drops new table/columns
3. Orchestration revert — stop calling `record_usage` (no-op if service removed)

**Note:** Lifetime counters lost on downgrade — acceptable for rollback.

---

## Env / deploy

- [ ] **Không cần env vars mới** v1
- [ ] `render.yaml` — không đổi (no new secrets)
- [ ] Run migration on deploy before API rollout

---

## Estimated timeline

| Phase | Duration |
|-------|----------|
| A | 1 day |
| B | 0.5 day |
| C | 1 day |
| D | 0.5 day |
| E | 1 day |
| F | 0.5 day |
| **Total** | **4–5 days** |
