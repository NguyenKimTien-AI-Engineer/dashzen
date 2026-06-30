# 02 — Token Usage (Frontend / Studio)

> **Trạng thái:** Planned
>
> **Master plan:** [`../../../token-usage.md`](../../../token-usage.md)
>
> **Backend dependency:** [`../Backend/usage/01-token-usage-backend.md`](../Backend/usage/01-token-usage-backend.md) — Phase D API schemas + SSE events

---

## 1. Mục tiêu UI

| Vị trí | Nội dung | Trạng thái |
|--------|----------|------------|
| **Thinking header** (live + persisted) | `In 12.4K · Out 1.8K` căn phải | Planned |
| **Settings → Account** | Lifetime input / output / total | Planned |
| **Conversation total** | — | Out of scope v1 |

### Reference mockup

Header Thinking (Gemini-style):

```
⌃⌄  Thinking                          In 12.4K · Out 1.8K
    📄 The user is asking 'tôi vừa hỏi cái gì'...
```

Token display **không** nằm trong footer (timestamp / copy icons) — chỉ trên header Thinking.

---

## 2. Hiện trạng Studio

| File | Vai trò |
|------|---------|
| `modules/task/components/chat/ActivityBlocks.tsx` | `ThinkingPanel` — header button |
| `modules/task/components/chat/ChatMessageList.tsx` | Live + persisted ThinkingPanel |
| `modules/task/contexts/task-reducer.ts` | Stream state — chưa có usage |
| `modules/task/types/task-state.ts` | `TaskState` — chưa có `turnUsage` |
| `modules/task/types/stream-events.ts` | Chưa có `usage_update` |
| `modules/task/types/activity-log.ts` | Chưa có `usage` field |
| `modules/auth/types/auth.ts` | `User` — chưa có `usage` |
| `modules/settings/components/AccountSettingsPanel.tsx` | Account UI |

---

## 3. Type changes

### 3.1 `modules/task/types/activity-log.ts`

```typescript
export type ActivityLogUsage = {
  input_tokens: number;
  output_tokens: number;
};

export type ActivityLogPayload = {
  type: "activity_log";
  version: number;
  header_title: string;
  usage?: ActivityLogUsage;
  sections: ActivitySectionPayload[];
};
```

### 3.2 `modules/task/types/stream-events.ts`

```typescript
export type UsageUpdateEvent = {
  type: "usage_update";
  turn_input_tokens: number;
  turn_output_tokens: number;
  delta_input: number;
  delta_output: number;
};

export type StreamDoneEvent = {
  type: "stream_done";
  partial_message_id?: string | null;
  turn_input_tokens?: number | null;
  turn_output_tokens?: number | null;
};
```

Update `StreamEvent` union + `KNOWN_TYPES` set.

### 3.3 `modules/task/types/task-state.ts`

```typescript
export type TurnUsage = {
  inputTokens: number;
  outputTokens: number;
};

export type TaskState = {
  // ...existing
  turnUsage: TurnUsage | null;
};

export const initialTaskState = (taskId: string): TaskState => ({
  // ...
  turnUsage: null,
});
```

### 3.4 `modules/auth/types/auth.ts`

```typescript
export type UsageSummary = {
  input_tokens: number;
  output_tokens: number;
};

export type User = {
  // ...existing
  usage?: UsageSummary;
};
```

### 3.5 `modules/task/types/api.ts`

```typescript
export type Message = {
  // ...existing
  prompt_tokens: number | null;
  output_tokens?: number | null;
  turn_id?: string | null;
};
```

---

## 4. `formatTokens` utility

**File:** `apps/studio/modules/task/lib/format-tokens.ts`

```typescript
/**
 * Compact token count for UI (Thinking header, Settings).
 * Uses 1 decimal for K/M suffixes.
 */
export function formatTokens(count: number): string {
  if (!Number.isFinite(count) || count < 0) return "0";
  if (count < 1_000) return count.toLocaleString("en-US");
  if (count < 1_000_000) {
    const k = count / 1_000;
    return `${trimTrailingZero(k.toFixed(1))}K`;
  }
  const m = count / 1_000_000;
  return `${trimTrailingZero(m.toFixed(1))}M`;
}

function trimTrailingZero(s: string): string {
  return s.endsWith(".0") ? s.slice(0, -2) : s;
}

export function formatUsagePair(input: number, output: number): string {
  return `In ${formatTokens(input)} · Out ${formatTokens(output)}`;
}
```

**Tests:** `apps/studio/modules/task/lib/format-tokens.test.ts`

| Input | Output |
|-------|--------|
| 0, 0 | `In 0 · Out 0` |
| 842, 120 | `In 842 · Out 120` |
| 12400, 1850 | `In 12.4K · Out 1.8K` |
| 1500000, 200000 | `In 1.5M · Out 200K` |

---

## 5. Stream pipeline

### 5.1 `map-stream-event.ts`

```typescript
case "usage_update":
  return {
    type: "USAGE_UPDATE",
    inputTokens: event.turn_input_tokens,
    outputTokens: event.turn_output_tokens,
  };

case "stream_done":
  return {
    type: "STREAM_END",
    turnUsage: event.turn_input_tokens != null
      ? { inputTokens: event.turn_input_tokens, outputTokens: event.turn_output_tokens ?? 0 }
      : undefined,
  };
```

### 5.2 `task-reducer.ts` actions

```typescript
| { type: "USAGE_UPDATE"; inputTokens: number; outputTokens: number }
| { type: "STREAM_END"; turnUsage?: TurnUsage }
```

**Reducer cases:**

```typescript
case "STREAM_START":
  return { ...state, turnUsage: null, ... };

case "USAGE_UPDATE":
  return {
    ...state,
    turnUsage: {
      inputTokens: action.inputTokens,
      outputTokens: action.outputTokens,
    },
  };

case "STREAM_END":
  return {
    ...state,
    turnUsage: action.turnUsage ?? state.turnUsage, // keep last if stream_done has totals
    // ...existing reset fields — turnUsage cleared here or kept until cache refresh
    turnUsage: null,
  };
```

**Quyết định v1:** Clear `turnUsage` on `STREAM_END` — persisted message sẽ có `activity_log.usage` sau cache invalidation.

### 5.3 `task-connection.tsx`

Handle raw SSE `usage_update` — mirror `stream_done` pattern:

```typescript
if (event.type === "usage_update") {
  onEventRef.current({
    type: "USAGE_UPDATE",
    inputTokens: event.turn_input_tokens,
    outputTokens: event.turn_output_tokens,
  });
}
```

### 5.4 Cache invalidation

Sau `STREAM_END` trong `task-context.tsx`:

```typescript
import { useQueryClient } from "@tanstack/react-query";

// In stream end handler:
queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
queryClient.invalidateQueries({ queryKey: ["tasks", taskId, "messages"] });
```

Đảm bảo Settings usage và persisted Thinking usage refresh.

---

## 6. `ThinkingPanel` component

**File:** `modules/task/components/chat/ActivityBlocks.tsx`

### 6.1 Props extension

```typescript
type ThinkingPanelProps = {
  activityLog: ActivityLogPayload;
  usage?: { inputTokens: number; outputTokens: number } | null;
  isActive?: boolean;
  collapsed?: boolean;
  onToggle?: () => void;
  defaultCollapsed?: boolean;
};
```

### 6.2 Resolve usage (priority)

```typescript
const resolvedUsage = usage ?? (activityLog.usage
  ? { inputTokens: activityLog.usage.input_tokens, outputTokens: activityLog.usage.output_tokens }
  : null);
```

### 6.3 Header layout change

```tsx
<button
  type="button"
  onClick={handleToggle}
  className="group flex w-full items-center gap-2 text-left text-sm ..."
  aria-expanded={!collapsed}
>
  <ChevronsUpDown className="size-4 shrink-0 ..." aria-hidden />
  <span className="line-clamp-2 flex-1 font-medium capitalize text-foreground/75">
    {headerTitle}
  </span>
  {resolvedUsage ? (
    <span
      className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground/70"
      aria-label={`Token usage: ${resolvedUsage.inputTokens} input, ${resolvedUsage.outputTokens} output`}
    >
      {formatUsagePair(resolvedUsage.inputTokens, resolvedUsage.outputTokens)}
    </span>
  ) : null}
</button>
```

### 6.4 Visual spec

| Property | Value |
|----------|-------|
| Font | `font-mono text-xs tabular-nums` |
| Color | `text-muted-foreground/70` |
| Position | Flex row, title `flex-1`, usage `shrink-0` right |
| Hover | Không đổi — usage static |
| Collapsed/expanded | Usage **luôn hiển thị** trên header |
| Active streaming | Số update live khi `usage_update` arrives |
| Narrow mobile | Usage có thể wrap — `hidden sm:inline` **không** dùng v1 (user cần thấy) |

### 6.5 Accessibility

- `aria-label` trên usage span mô tả đầy đủ số
- Không dùng màu đỏ/vàng — informational only

---

## 7. `ChatMessageList` wiring

**File:** `modules/task/components/chat/ChatMessageList.tsx`

### 7.1 Destructure `turnUsage` from `useTask`

Update `useTask` / `TaskContext` to expose `turnUsage`.

### 7.2 Persisted assistant groups

```tsx
{activityLog ? (
  <ThinkingPanel
    activityLog={activityLog}
    usage={activityLog.usage
      ? { inputTokens: activityLog.usage.input_tokens, outputTokens: activityLog.usage.output_tokens }
      : null}
    defaultCollapsed
  />
) : null}
```

`getAssistantGroupActivityLog` — không cần đổi nếu `usage` nằm trong activity_log root.

### 7.3 Live streaming panel

```tsx
{showLiveThinking ? (
  <ThinkingPanel
    activityLog={liveActivityLog}
    usage={turnUsage}
    isActive={hasRunningAgents || Boolean(thinkingText.trim())}
    collapsed={thinkingPanelCollapsed}
    onToggle={toggleThinkingPanel}
  />
) : null}
```

---

## 8. `useTask` hook

**File:** `modules/task/hooks/useTask.ts`

```typescript
return {
  ...
  turnUsage: state.turnUsage,
};
```

---

## 9. Settings — Account panel

**File:** `modules/settings/components/AccountSettingsPanel.tsx`

### 9.1 Section markup

Insert after Email block, before Password:

```tsx
<div className="space-y-3 border-t pt-6">
  <div>
    <p className="text-sm font-medium">Token usage</p>
    <p className="text-sm text-muted-foreground">
      Total tokens used since you joined
      {user.created_at
        ? ` ${new Date(user.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`
        : ""}
      .
    </p>
  </div>
  <dl className="grid max-w-sm grid-cols-2 gap-x-4 gap-y-2 text-sm">
    <dt className="text-muted-foreground">Input</dt>
    <dd className="font-mono tabular-nums text-right">
      {formatTokens(user.usage?.input_tokens ?? 0)}
    </dd>
    <dt className="text-muted-foreground">Output</dt>
    <dd className="font-mono tabular-nums text-right">
      {formatTokens(user.usage?.output_tokens ?? 0)}
    </dd>
    <dt className="font-medium">Total</dt>
    <dd className="font-mono tabular-nums text-right font-medium">
      {formatTokens(
        (user.usage?.input_tokens ?? 0) + (user.usage?.output_tokens ?? 0),
      )}
    </dd>
  </dl>
</div>
```

### 9.2 Import

```typescript
import { formatTokens } from "@/modules/task/lib/format-tokens";
```

### 9.3 Empty state

Nếu `usage` undefined (API cũ) → hiển thị `0` — không crash.

### 9.4 Không thêm tab Settings mới

Giữ trong Account — đủ cho v1. Search settings vẫn tìm "Account".

---

## 10. Message normalization

**Files:**
- `modules/task/lib/normalize-messages.ts` (nếu có)
- `modules/task/lib/patch-message-cache.ts`

Đảm bảo `activity_log.usage` preserved khi normalize/patch:

```typescript
activity_log: msg.activity_log ?? undefined,
// usage nested inside activity_log — no extra work if whole object kept
```

Update tests in `patch-message-cache.test.ts`, `normalize-messages.test.ts`.

---

## 11. `useTask` context provider

**File:** `modules/task/contexts/task-context.tsx`

Wire `USAGE_UPDATE` dispatch từ stream handler.

On `STREAM_END`:

```typescript
queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
```

---

## 12. Files checklist

### Create

| File | Mô tả |
|------|-------|
| `modules/task/lib/format-tokens.ts` | Formatter |
| `modules/task/lib/format-tokens.test.ts` | Unit tests |

### Modify

| File | Thay đổi |
|------|----------|
| `modules/task/types/activity-log.ts` | `ActivityLogUsage` |
| `modules/task/types/stream-events.ts` | `UsageUpdateEvent` |
| `modules/task/types/task-state.ts` | `turnUsage` |
| `modules/task/types/api.ts` | `output_tokens`, `turn_id` |
| `modules/auth/types/auth.ts` | `usage` on User |
| `modules/task/lib/map-stream-event.ts` | Map new events |
| `modules/task/contexts/task-reducer.ts` | `USAGE_UPDATE` |
| `modules/task/contexts/task-connection.tsx` | Parse SSE |
| `modules/task/contexts/task-context.tsx` | Invalidate queries |
| `modules/task/hooks/useTask.ts` | Expose turnUsage |
| `modules/task/components/chat/ActivityBlocks.tsx` | Header usage |
| `modules/task/components/chat/ChatMessageList.tsx` | Wire props |
| `modules/settings/components/AccountSettingsPanel.tsx` | Usage section |
| `modules/task/lib/patch-message-cache.ts` | Preserve fields |
| Tests | patch-message-cache, normalize-messages |

---

## 13. Manual QA script

1. **Live usage**
   - Mở chat, gửi message với thinking enabled
   - Trong lúc stream: mở Thinking panel → header hiện `In … · Out …`
   - Số tăng khi sub-agent chạy (nếu spawn)

2. **Persisted usage**
   - Refresh page sau turn complete
   - Thinking panel trên message cũ vẫn hiện usage

3. **Settings**
   - Mở Settings → Account
   - Input / Output / Total khớp (xấp xỉ) với tổng các turns đã chạy sau deploy

4. **No thinking**
   - Turn không có activity log content → không hiện ThinkingPanel → **không hiện usage** (acceptable v1)
   - *Phase 2 optional:* hiện usage dưới assistant message nếu không có thinking

5. **Mobile width**
   - Header không vỡ layout 320px

6. **Accessibility**
   - Screen reader đọc aria-label usage

---

## 14. Out of scope UI (Phase 2)

| Feature | Ghi chú |
|---------|---------|
| Usage khi không có Thinking panel | Hiện dưới `MessageActions` |
| Task sidebar conversation total | Badge trên task item |
| Tooltip breakdown per source | Orchestrator vs sub-agent |
| Animated counter | Optional polish |
| Settings tab "Usage" riêng | Charts |

---

## 15. Verification commands

```bash
cd apps/studio
pnpm test modules/task/lib/format-tokens.test.ts
pnpm test modules/task/lib/patch-message-cache.test.ts
pnpm lint
pnpm typecheck  # if configured
```

Manual: `pnpm dev` + chat against local API with migration applied.
