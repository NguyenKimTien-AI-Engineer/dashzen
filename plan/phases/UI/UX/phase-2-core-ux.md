# Phase 2 — Core UX

> **Mục tiêu:** Streaming mượt không flicker, HITL đầy đủ, resilience khi mất kết nối, performance cho hội thoại dài.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) §19 Phase 2, §6.4–§6.5, §7.3–§7.4, §8.1, §10, §12–§16 (subset)
>
> **Ưu tiên:** P1–P2 | **Phụ thuộc:** Phase 1 MVP hoàn thành

---

## 1. Tại sao Phase 2 quan trọng

Phase 1 ship được happy path. Phase 2 xử lý **core UX gaps** so với LeadZen reference:

- Assistant message flat bubble → **interleaved timeline** (tool/thinking/agent xen kẽ text)
- Refresh page mất context stream → **normalise_messages** rebuild đầy đủ
- Mất SSE giữa chừng → **ReconnectBanner** + retry/errorKind
- Hội thoại dài lag → **virtualized list**
- Context đầy → **donut + compact**

> §19 ghi rõ: nhiều mục Phase 2 được **promote từ Phase 3** — không defer thêm.

---

## 2. Deliverables checklist

### 2.1 Interleaved streaming timeline (§10.1)

- [ ] `streamingActivities[]` trong `task-reducer` suốt stream
- [ ] Assistant message render blocks xen kẽ:

```
[text chunk] [thinking block] [tool chip] [text chunk] [agent block] ...
```

- [ ] Tránh flicker khi tool chèn giữa text stream
- [ ] `STREAM_END` → bridge giữ streaming state đến `SET_MESSAGES` (no layout jump)
- [ ] Reducer actions bổ sung: `STREAM_THINKING_DELTA`, `ASK_PENDING`, `ASK_SUBMITTED`

### 2.2 Message reload & normalization (§10.2)

- [ ] `GET /messages` → `normaliseMessages()` pure function
- [ ] `reconstructAgentCalls()` — rebuild `AgentActivityBlock` từ `AgentRun.activities`
- [ ] `thinkingByMessageId` map — restore thinking blocks
- [ ] `toolResults` session cache — backfill chip results
- [ ] Compact boundary — ẩn messages trước `role: compact` node
- [ ] Unit test 100% cho `normaliseMessages`, `reconstructAgentCalls`

### 2.3 Extended thinking display (§6.1)

- [ ] `ThinkingBlock` — collapsible muted block, icon 🧠
- [ ] SSE `main_think` → `STREAM_THINKING_DELTA`
- [ ] Agent block: `agent_think` trong timeline
- [ ] `prefers-reduced-motion` — tắt animation streaming text

### 2.4 Human-in-the-loop nâng cao (§6.3, §10.3)

- [ ] `ask_user` form ActionCard — input fields → `POST /gates/ask`
- [ ] `gateToAgentId` map — route ActionCard vào đúng agent block (sub-agent tools)
- [ ] Gate feedback text trong tool chip sau approve/reject
- [ ] ActionCard timeout 5 min → warning toast + auto-reject option
- [ ] Data connector approval ActionCard + mô tả connector

### 2.5 Regenerate & branch navigation (§10.4)

| Feature | API | UI |
|---------|-----|-----|
| Regenerate | Fork message tree + new stream | Nút ↻ trên assistant message (hover) |
| Edit message | Fork từ user message | Inline edit → resend |
| Branch nav | `branchInfo` từ `GET /messages` | `‹ 2/3 ›` trên message có siblings |
| `SET_TIP` | SSE hoặc API | Hint khi có nhánh mới |

- [ ] Reducer: `REMOVE_MESSAGE` cho edit/regenerate fork

### 2.6 Context donut & compact (§6.4)

- [ ] `ContextDonut` — % context fill (`GET /v1/llm/budget` + token count)
- [ ] Nút **Compact** khi > 50% (`isCompactEligible`)
- [ ] `POST /v1/tasks/{id}/compact` → refetch messages
- [ ] Tooltip: "Context X% full — compact để tối ưu"
- [ ] ARIA: `role="progressbar"` + `aria-valuenow`
- [ ] Compact success toast

### 2.7 TaskConnection resilience (§7.3, §7.4, §10.5)

| Pattern | Chi tiết |
|---------|----------|
| Pre-stream retry | 2× retry nếu fail trước first byte |
| Read stall | Abort + `connection_lost` sau 35s không data |
| 409 handling | `still_processing` → auto-retry sau 105s |
| Stop before send | Await `stopInFlightRef` trước stream mới |
| `errorKind` | `still_processing` \| `connection_lost` \| `stream_error` |

**UI theo errorKind:**

| `errorKind` | UI |
|-------------|-----|
| `stream_error` | Red error card + "Thử lại" |
| `connection_lost` | ReconnectBanner + auto-retry (2s, 4s, 8s) |
| `still_processing` | Yellow warning + auto-retry 105s |

### 2.8 ReconnectBanner (§6.5)

- [ ] Hiện khi SSE ngắt (network, server restart)
- [ ] Auto-retry exponential backoff
- [ ] Biến mất khi reconnect thành công
- [ ] Agent vẫn chạy khi mất kết nối → "Agent đang chạy..."
- [ ] Nút [Thử lại] manual

### 2.9 Canvas nâng cao (§8.1)

- [ ] **Resize handle** giữa chat và canvas (drag tỷ lệ)
- [ ] Responsive preview toolbar: Desktop / Tablet / Mobile
- [ ] Viewport resize iframe/container theo breakpoint
- [ ] Persist viewport chọn trong localStorage
- [ ] Artifact cache: cùng hash → không reload canvas

### 2.10 Chat input bổ sung (§5)

- [ ] **ScrollToBottomButton** FAB khi user scroll lên
- [ ] Token estimate ~N tokens (`tokens_per_char`)
- [ ] **File attach** 📎 — CSV, JSON schema
- [ ] `ensureTask()` — tạo task trước upload nếu chưa có taskId
- [ ] `persistUploadFiles` link vào pending user message
- [ ] Drag & drop file vào textarea area
- [ ] Quick Action Chips (Home): Design Dashboard, Connect Data, From Template
- [ ] Copy message button (hover metadata)

### 2.11 Sidebar bổ sung (§4)

- [ ] Search filter recents (debounced 300ms)
- [ ] Context menu: Rename, Delete, Duplicate
- [ ] Rate limit: "X/20 dashboard hôm nay" trong sidebar
- [ ] Disable "New Dashboard" + tooltip khi hit limit
- [ ] Prefetch task khi hover sidebar item

### 2.12 Performance (§13)

- [ ] `@tanstack/react-virtual` cho `ChatMessageList` (≥ 20 messages)
- [ ] Overscan 3 items; dynamic height estimate + measure
- [ ] `React.memo`: ChatMessage, AgentActivityBlock, DashboardCanvas, SidebarRecents item
- [ ] Reducer selectors: `useCallback` / `useMemo`
- [ ] Lazy load: `DashboardCanvas`, Settings page
- [ ] shiki — chỉ import ngôn ngữ cần thiết
- [ ] TanStack Query `staleTime: 30_000` task list

### 2.13 Rate limit UI (§15.3)

- [ ] `rateLimitStore` — `X-RateLimit-Remaining` từ headers
- [ ] `useRateLimit()` hook
- [ ] 429 toast + cooldown timer
- [ ] Rate limited message card trong chat

### 2.14 Accessibility & keyboard (§12)

- [ ] `Escape` — cancel streaming / close modal
- [ ] `Cmd+/` — toggle sidebar
- [ ] `AgentActivityBlock`: `role="region"` + `aria-expanded`
- [ ] Streaming text: `aria-live="assertive"` trong bubble
- [ ] `ScrollToBottomButton`: `aria-label="Cuộn xuống tin nhắn mới nhất"`

### 2.15 Testing (§16)

| Layer | Tool | Target |
|-------|------|--------|
| Unit | Vitest | `task-reducer`, `normaliseMessages`, `reconstructAgentCalls` — 100% |
| Component | Testing Library | ChatInput, ActionCard, AgentActivityBlock |
| Integration | MSW | `useTask`, SSE flow mock |
| E2E | Playwright | login → send → stream → canvas (happy path) |

**Critical test cases:**

- [ ] `STREAM_START` → optimistic message
- [ ] Interleaved delta + tool + agent events
- [ ] 409 → auto-retry flow
- [ ] Disconnect → reconnect → restore state
- [ ] Gate approve/reject → stream resume

---

## 3. Definition of done

Phase 2 hoàn thành khi:

1. Assistant message hiển thị interleaved timeline không flicker
2. Refresh page restore đầy đủ thinking, tools, agent blocks
3. Mất kết nối SSE → ReconnectBanner + retry theo errorKind
4. User compact context khi > 50%, thấy donut %
5. Regenerate / branch navigation hoạt động
6. `ask_user` form ActionCard resolve được
7. Attach file trước/sau tạo task
8. Hội thoại 50+ messages scroll mượt (virtualized)
9. Rate limit hiển thị rõ, không gửi khi bị chặn

---

## 4. Phụ thuộc & rủi ro

| Rủi ro | Mitigation |
|--------|------------|
| `normaliseMessages` phức tạp | Unit test first, mirror BE message schema |
| Virtualization + dynamic height | Estimate height, measure on mount |
| Branch API chưa stable | Coordinate với `06-api-contracts.md` |
| Gate timeout UX | Default 5 min align backend FSM |

---

## 5. Tiếp theo

Xem [`phase-3-polish-scale.md`](./phase-3-polish-scale.md) cho export, prefs, i18n, discovery.
