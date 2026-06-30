# 01 — Token Usage (Backend)

> **Trạng thái:** Planned
>
> **Master plan:** [`../../../token-usage.md`](../../../token-usage.md)
>
> **Tiền đề:** Agent orchestration Done — `main_loop`, `agent_loop`, streaming SSE, `messages` table

---

## 1. Hiện trạng (as-built)

| Thành phần | Trạng thái |
|------------|------------|
| `LLMDelta.prompt_tokens` / `output_tokens` | **Done** — providers populate on stream `done` |
| `messages.prompt_tokens` | **Done** — per orchestrator iteration |
| `messages.output_tokens` | **Chưa có** |
| `client.chat()` usage | **Chưa có** — returns `str` only |
| Sub-agent usage tracking | **Chưa có** |
| User/task lifetime counters | **Chưa có** |
| `usage_update` SSE event | **Chưa có** |
| Prometheus `agent_token_total` | **Done** — prompt only, orchestrator only |

---

## 2. Migration `010_token_usage.py`

**File:** `packages/db/alembic/versions/010_token_usage.py`

**Revision chain:** `009_google_oauth` → `010_token_usage`

### 2.1 Upgrade

```python
def upgrade() -> None:
    # llm_usage_events table
    op.create_table(
        "llm_usage_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.UUID(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("agent_name", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_llm_usage_user_id", "llm_usage_events", ["user_id"])
    op.create_index("ix_llm_usage_task_id", "llm_usage_events", ["task_id"])
    op.create_index("ix_llm_usage_turn_id", "llm_usage_events", ["turn_id"])
    op.create_index("ix_llm_usage_user_created", "llm_usage_events", ["user_id", "created_at"])

    # users counters
    op.add_column("users", sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"))

    # tasks counters
    op.add_column("tasks", sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("tasks", sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"))

    # messages extension
    op.add_column("messages", sa.Column("output_tokens", sa.Integer(), nullable=True))
    op.add_column("messages", sa.Column("turn_id", sa.UUID(), nullable=True))
    op.create_index("ix_messages_turn_id", "messages", ["turn_id"])
```

### 2.2 Downgrade

Drop indexes + columns reverse order. Không backfill v1 — counters start at 0 cho existing users (acceptable: historical usage unknown).

### 2.3 Backfill (optional — defer)

Nếu cần approximate historical data:

```sql
-- KHÔNG khuyến nghị v1 — prompt_tokens per message không phải turn total
-- Chỉ chạy nếu product yêu cầu
UPDATE users u SET total_input_tokens = (
  SELECT COALESCE(SUM(m.prompt_tokens), 0)
  FROM messages m JOIN tasks t ON m.task_id = t.id
  WHERE t.user_id = u.id AND m.prompt_tokens IS NOT NULL
);
```

**Quyết định v1:** Không backfill — lifetime counter bắt đầu từ deploy.

---

## 3. ORM models

### 3.1 `packages/db/src/db/models/llm_usage_event.py`

```python
class LlmUsageEvent(Base):
    __tablename__ = "llm_usage_events"
    __table_args__ = (
        Index("ix_llm_usage_user_id", "user_id"),
        Index("ix_llm_usage_task_id", "task_id"),
        Index("ix_llm_usage_turn_id", "turn_id"),
        Index("ix_llm_usage_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID]
    user_id: Mapped[uuid.UUID]
    task_id: Mapped[uuid.UUID]
    turn_id: Mapped[uuid.UUID]
    message_id: Mapped[uuid.UUID | None]
    source: Mapped[str]  # orchestrator | sub_agent | compaction | title
    agent_name: Mapped[str | None]
    model: Mapped[str | None]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    created_at: Mapped[datetime]
```

Export trong `db/models/__init__.py`.

### 3.2 Update existing models

**`user.py`:**

```python
total_input_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
total_output_tokens: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
```

**`task.py`:** same pattern.

**`message.py`:**

```python
output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
turn_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
```

---

## 4. `usage_service.py`

**File:** `packages/db/src/db/services/usage_service.py`

### 4.1 Types

```python
UsageSource = Literal["orchestrator", "sub_agent", "compaction", "title"]

@dataclass(frozen=True)
class UsageTotals:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
```

### 4.2 `record_usage`

```python
async def record_usage(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    turn_id: uuid.UUID,
    source: UsageSource,
    input_tokens: int,
    output_tokens: int,
    message_id: uuid.UUID | None = None,
    agent_name: str | None = None,
    model: str | None = None,
) -> UsageTotals | None:
    """
  1. If input_tokens == 0 and output_tokens == 0: return None (skip)
  2. INSERT llm_usage_events
  3. UPDATE users SET total_* += delta WHERE id = user_id
  4. UPDATE tasks SET total_* += delta WHERE id = task_id AND user_id = user_id
  5. Return UsageTotals(input_tokens, output_tokens)
    """
```

**Notes:**
- Không `commit()` — caller owns transaction boundary (match `message_service` pattern)
- `flush()` after insert for FK visibility
- Task update must include `user_id` guard

### 4.3 Getters

```python
async def get_user_usage(db: AsyncSession, user_id: uuid.UUID) -> UsageTotals:
    # SELECT total_input_tokens, total_output_tokens FROM users WHERE id = ?

async def get_task_usage(db: AsyncSession, task_id: uuid.UUID, user_id: uuid.UUID) -> UsageTotals:
    # SELECT ... FROM tasks WHERE id = ? AND user_id = ?

async def sum_turn_usage(db: AsyncSession, turn_id: uuid.UUID) -> UsageTotals:
    # SELECT SUM(input_tokens), SUM(output_tokens) FROM llm_usage_events WHERE turn_id = ?
    # Fallback nếu cần verify denormalized
```

### 4.4 Tests

**File:** `packages/db/tests/test_usage_service.py`

| Test | Assert |
|------|--------|
| `test_record_usage_bumps_user_and_task` | Counters += delta |
| `test_record_usage_zero_skips` | No row inserted |
| `test_get_task_usage_wrong_user` | Returns 0 or raises — match task_service pattern |
| `test_cascade_delete_user` | Events deleted with user |

---

## 5. Core LLM changes

### 5.1 `packages/core/src/core/llm/types.py`

```python
@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None

    def or_zero(self) -> tuple[int, int]:
        return self.input_tokens or 0, self.output_tokens or 0

@dataclass(frozen=True)
class LLMChatResult:
    content: str
    usage: LLMUsage = field(default_factory=LLMUsage)
```

### 5.2 `packages/core/src/core/llm/client.py`

```python
class LLMClient(Protocol):
    async def chat(...) -> LLMChatResult: ...
    async def stream(...) -> AsyncGenerator[LLMDelta, None]: ...
```

### 5.3 Provider `chat()` updates

**OpenAI** (`openai.py`):

```python
data = resp.json()
usage = data.get("usage") or {}
return LLMChatResult(
    content=data["choices"][0]["message"]["content"] or "",
    usage=LLMUsage(
        input_tokens=usage.get("prompt_tokens"),
        output_tokens=usage.get("completion_tokens"),
    ),
)
```

**Anthropic** (`anthropic.py`):

```python
usage = data.get("usage") or {}
return LLMChatResult(
    content=extract_text(data),
    usage=LLMUsage(
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    ),
)
```

**Gemini, OpenRouter, Ollama:** tương tự — parse provider-specific usage block.

### 5.4 Core tests

Update mocks in:
- `packages/core/tests/` (nếu có chat tests)
- `apps/api/tests/test_stream_api.py` — `chat()` returns `LLMChatResult`

---

## 6. `UsageAccumulator` helper

**File:** `packages/agents/src/agents/usage/accumulator.py` (optional, recommended)

```python
@dataclass
class UsageAccumulator:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def add_delta(self, delta: UsageTotals) -> None:
        self.add(delta.input_tokens, delta.output_tokens)
```

Dùng trong `main_loop` cho turn-level running total.

---

## 7. `main_loop.py` changes

### 7.1 New locals at turn start

```python
turn_id = uuid.uuid4()
turn_usage = UsageAccumulator()
```

### 7.2 Pass `turn_id` to `ToolContext`

```python
tool_ctx = ToolContext(
  ...
  turn_id=turn_id,
)
```

### 7.3 Stream iteration — capture both tokens

```python
prompt_tokens: int | None = None
output_tokens: int | None = None

async for delta in client.stream(...):
    ...
    elif delta.kind == "done":
        prompt_tokens = delta.prompt_tokens
        output_tokens = delta.output_tokens
        break

in_t, out_t = prompt_tokens or 0, output_tokens or 0
if in_t or out_t:
    recorded = await record_usage(
        ctx.db,
        user_id=ctx.user_id,
        task_id=ctx.task_id,
        turn_id=turn_id,
        source="orchestrator",
        input_tokens=in_t,
        output_tokens=out_t,
        message_id=None,  # set after create_message
        model=getattr(client, "_model", None),  # or settings
    )
    if recorded:
        turn_usage.add_delta(recorded)
        emit_logged(UsageUpdateEvent(
            turn_input_tokens=turn_usage.input_tokens,
            turn_output_tokens=turn_usage.output_tokens,
            delta_input=recorded.input_tokens,
            delta_output=recorded.output_tokens,
        ))
```

### 7.4 `create_message` — add fields

```python
asst_msg = await create_message(
    ...
    prompt_tokens=prompt_tokens,
    output_tokens=output_tokens,
    turn_id=turn_id,
)
```

Update `message_service.create_message` signature.

### 7.5 End of turn — activity log usage

Trong `ActivityLog` dataclass (`activity_log.py`):

```python
@dataclass
class ActivityLog:
    header_title: str = ""
    usage_input_tokens: int = 0
    usage_output_tokens: int = 0
    sections: list[ActivitySection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = { "type": "activity_log", "version": 1, "header_title": self.header_title, "sections": ... }
        if self.usage_input_tokens or self.usage_output_tokens:
            d["usage"] = {
                "input_tokens": self.usage_input_tokens,
                "output_tokens": self.usage_output_tokens,
            }
        return d
```

Trước `_persist_activity_log()` final:

```python
activity_acc.set_usage(turn_usage.input_tokens, turn_usage.output_tokens)
```

### 7.6 `StreamDoneEvent` — include totals

```python
emit_logged(StreamDoneEvent(
    turn_input_tokens=turn_usage.input_tokens,
    turn_output_tokens=turn_usage.output_tokens,
))
```

### 7.7 Title task — pass turn context

`try_set_title` cần `user_id`, `turn_id` để record title usage:

```python
title_task = asyncio.create_task(
    try_set_title(ctx.db, ctx.task_id, user_message, turn_number, user_id=ctx.user_id, turn_id=turn_id)
)
```

Title completion callback có thể emit `UsageUpdateEvent` nếu title finish sau main response — FE nên accept late updates hoặc chỉ update account total silently.

**Quyết định v1:** Title usage vẫn record DB + bump counters; emit `usage_update` nếu stream chưa done, else skip SSE (account total refreshed on next `/me`).

### 7.8 Error path

Trong `except` block trước metrics — vẫn persist partial `turn_usage` đã accumulate (đã flush per iteration).

---

## 8. `agent_loop.py` changes

### 8.1 Stream done handling

```python
input_t, output_t = 0, 0
async for delta in client.stream(...):
    ...
    elif delta.kind == "done":
        input_t = delta.prompt_tokens or 0
        output_t = delta.output_tokens or 0
        break

if ctx.turn_id and (input_t or output_t):
    from db.services.usage_service import record_usage
    recorded = await record_usage(
        ctx.db,
        user_id=ctx.user_id,
        task_id=ctx.task_id,
        turn_id=ctx.turn_id,
        source="sub_agent",
        input_tokens=input_t,
        output_tokens=output_t,
        agent_name=agent_name,
    )
    if recorded:
        from agents.streaming.events import UsageUpdateEvent
        # Need turn-level accumulator on ToolContext OR re-query sum_turn_usage
        emit(UsageUpdateEvent(...))
```

### 8.2 Turn totals for SSE

**Option A (khuyến nghị):** `ToolContext` holds `UsageAccumulator` reference (mutable, shared with main_loop).

```python
@dataclass
class ToolContext:
    turn_usage: UsageAccumulator | None = None
```

`main_loop` sets `turn_usage=turn_usage` on ToolContext; sub-agents call `turn_usage.add()` + emit with updated totals.

**Option B:** Re-query `sum_turn_usage(db, turn_id)` after each record — simpler but extra DB roundtrip per sub-agent iteration.

---

## 9. `compaction.py` changes

### 9.1 Signature extension

```python
async def compact_if_over_budget(
    messages: list[LLMMessage],
    db: AsyncSession,
    task_id: uuid.UUID,
    state: CompactionState,
    *,
    leaf_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
) -> tuple[list[LLMMessage], bool]:
```

### 9.2 `_summarize_messages` → record usage

```python
async def _summarize_messages(
    messages: list[LLMMessage],
    *,
    db: AsyncSession | None = None,
    user_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
) -> str:
    result = await client.chat([LLMMessage(role="user", content=prompt)], ...)
    in_t, out_t = result.usage.or_zero()
    if db and user_id and task_id and turn_id and (in_t or out_t):
        await record_usage(..., source="compaction", input_tokens=in_t, output_tokens=out_t)
    return result.content
```

### 9.3 `manual_compact` API endpoint

Nếu có route gọi `manual_compact` — tạo `turn_id` riêng hoặc `turn_id=NULL` với source compaction. **Quyết định:** manual compact dùng `turn_id=uuid4()` one-off — vẫn bump task/user counters.

---

## 10. `task_title.py` changes

```python
async def generate_title(
    db: AsyncSession,
    task_id: uuid.UUID,
    conversation_so_far: str,
    turn_number: int,
    *,
    user_id: uuid.UUID | None = None,
    turn_id: uuid.UUID | None = None,
) -> str | None:
    result = await client.chat(...)
    in_t, out_t = result.usage.or_zero()
    if user_id and turn_id and (in_t or out_t):
        await record_usage(..., source="title", ...)
    ...
```

---

## 11. Streaming events

**File:** `packages/agents/src/agents/streaming/events.py`

```python
class UsageUpdateEvent(BaseModel):
    type: Literal["usage_update"] = "usage_update"
    turn_input_tokens: int
    turn_output_tokens: int
    delta_input: int
    delta_output: int

class StreamDoneEvent(BaseModel):
    type: Literal["stream_done"] = "stream_done"
    partial_message_id: str | None = None
    turn_input_tokens: int | None = None
    turn_output_tokens: int | None = None
```

Update `StreamEvent` union + `streaming/__init__.py` exports.

---

## 12. API layer

### 12.1 `packages/core/src/core/schemas/auth.py`

```python
class UsageSummary(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0

class UserResponse(BaseModel):
    ...
    usage: UsageSummary = Field(default_factory=UsageSummary)
```

### 12.2 `apps/api/src/api/auth_responses.py`

```python
async def build_user_response(session: AsyncSession, user: User) -> UserResponse:
    ...
    usage = await get_user_usage(session, user.id)
    return UserResponse(
        ...
        usage=UsageSummary(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        ),
    )
```

### 12.3 `apps/api/src/api/schemas/tasks.py`

```python
class ActivityLogUsage(BaseModel):
    input_tokens: int
    output_tokens: int

class ActivityLogResponse(BaseModel):
    ...
    usage: ActivityLogUsage | None = None
```

### 12.4 `message_service._enrich_message`

Parse `usage` từ activity_log JSON khi enrich — đã có trong `thinking` field.

### 12.5 `MessageResponse`

```python
class MessageResponse(BaseModel):
    ...
    prompt_tokens: int | None
    output_tokens: int | None = None
    turn_id: uuid.UUID | None = None
```

---

## 13. `ToolContext` update

**File:** `packages/tools/src/tools/context.py`

```python
@dataclass
class ToolContext:
    ...
    turn_id: uuid.UUID | None = None
    turn_usage: UsageAccumulator | None = None  # shared ref
```

---

## 14. Metrics extension

**File:** `apps/api/src/api/monitoring/metrics.py`

```python
def record_llm_usage(*, source: str, input_tokens: int, output_tokens: int) -> None:
    registry.inc("llm_usage_input_total", input_tokens, source=source)
    registry.inc("llm_usage_output_total", output_tokens, source=source)
```

Gọi từ `record_usage` hoặc orchestration sau record.

---

## 15. Files checklist (create / modify)

### Create

| File | Mô tả |
|------|-------|
| `packages/db/alembic/versions/010_token_usage.py` | Migration |
| `packages/db/src/db/models/llm_usage_event.py` | ORM |
| `packages/db/src/db/services/usage_service.py` | Service |
| `packages/db/tests/test_usage_service.py` | Tests |
| `packages/agents/src/agents/usage/accumulator.py` | Helper |
| `packages/agents/src/agents/usage/__init__.py` | Package init |

### Modify

| File | Thay đổi |
|------|----------|
| `packages/db/src/db/models/user.py` | Counter columns |
| `packages/db/src/db/models/task.py` | Counter columns |
| `packages/db/src/db/models/message.py` | output_tokens, turn_id |
| `packages/db/src/db/models/__init__.py` | Export LlmUsageEvent |
| `packages/db/src/db/services/message_service.py` | create_message params, enrich |
| `packages/core/src/core/llm/types.py` | LLMUsage, LLMChatResult |
| `packages/core/src/core/llm/client.py` | Protocol |
| `packages/core/src/core/llm/providers/*.py` | chat() return type (5 files) |
| `packages/agents/src/agents/orchestration/main_loop.py` | Full hook |
| `packages/agents/src/agents/orchestration/agent_loop.py` | Sub-agent hook |
| `packages/agents/src/agents/orchestration/activity_log.py` | usage in JSON |
| `packages/agents/src/agents/orchestration/task_title.py` | Title hook |
| `packages/agents/src/agents/context/compaction.py` | Compaction hook |
| `packages/agents/src/agents/streaming/events.py` | New events |
| `packages/tools/src/tools/context.py` | turn_id, turn_usage |
| `packages/core/src/core/schemas/auth.py` | UsageSummary |
| `apps/api/src/api/auth_responses.py` | Include usage |
| `apps/api/src/api/schemas/tasks.py` | Message + activity schemas |
| `apps/api/tests/test_stream_api.py` | Mock updates |

---

## 16. Verification commands

```bash
# Migration
cd packages/db && uv run alembic upgrade head

# Tests
uv run pytest packages/db/tests/test_usage_service.py -q
uv run pytest packages/agents/tests/ -q -k usage
uv run pytest apps/api/tests/test_stream_api.py -q

# Lint
uv run ruff check packages/db packages/agents packages/core apps/api
uv run mypy packages/db packages/agents packages/core
```
