# 08 — Artifact Preview Panel

> Split-view preview `spec.md` — markdown render, hot-reload on `file_artifact`.
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §8 | **Phụ thuộc:** [03](./03-task-context-and-reducer.md), BE `file_artifact` event

**Location:** `apps/studio/modules/task/components/preview/`  
**Phụ thuộc:** TaskProvider artifacts state

---

## 1. Mục tiêu

- [ ] 1. `SpecPreviewPanel` — panel phải task page
- [ ] 2. Hot-reload khi `file_artifact` SSE
- [ ] 3. Load initial từ `GET /artifacts` on mount
- [ ] 4. Collapse toggle — persist localStorage
- [ ] 5. **Không** WidgetRenderer — chỉ markdown preview Phase 1

---

## 2. Scope Phase 1 vs Phase 2

| Phase 1 | Phase 2+ |
|---------|----------|
| Markdown render `spec.md` | Live dashboard widgets |
| Toggle show/hide panel | Resize handle drag |
| Copy content button | Desktop/tablet/mobile preview |
| | Full-screen `/app/dashboard/[pageId]` |

Deliverable BE Phase 1: planner ghi `spec.md` → UI hiển thị nội dung spec dạng markdown.

---

## 3. Panel layout

```
┌─ Preview ──────────────── [−] [Copy] ─┐
│  spec.md                              │
│  ─────────────────────────────────    │
│  # Dashboard Specification            │
│  ## Title                             │
│  Revenue Dashboard                    │
│  ## Widgets                           │
│  - Widget 1: bar chart — ...          │
└───────────────────────────────────────┘
```

- Width: `35%` desktop, `0` khi collapsed
- Border-left separator
- Header: filename + actions

---

## 4. Data sources

| Source | Khi nào |
|--------|---------|
| `GET /artifacts` | Task page mount, sau STREAM_END |
| `file_artifact` SSE | Realtime during stream |
| Reducer `artifacts` map | UI immediate update |

Ưu tiên SSE content → overwrite local; refetch reconcile on end.

### 4.1 File priority

Phase 1 chỉ preview:

- `spec.md` — primary
- Fallback: first `kind=text` artifact nếu không có spec.md

Ignore `memory.md` trong preview (internal).

---

## 5. Empty states

| State | UI |
|-------|-----|
| No artifacts yet | "Spec sẽ hiện ở đây khi agent tạo file" + illustration |
| Loading | Skeleton document lines |
| Panel collapsed | Thin strip với expand button |

---

## 6. Dashboard Ready moment

Khi nhận `file_artifact` với `name=spec.md`:

1. Auto-expand panel nếu đang collapsed
2. Optional toast: "Dashboard spec đã sẵn sàng"
3. **Không** cần DashboardReadyCard riêng Phase 1 — preview panel đủ

Phase 2: thêm rich card trong chat stream.

---

## 7. Responsive

| Breakpoint | Behavior |
|------------|----------|
| `≥ lg` | Split view 65/35 |
| `< lg` | Preview below chat (stack) hoặc tab "Preview" |
| Mobile | Tab toggle Chat | Preview |

---

## 8. localStorage

| Key | Value |
|-----|-------|
| `dashzen:preview-collapsed` | `"true" \| "false"` |

Per-user browser — không sync server.

---

## 9. Copy action

Button Copy → `navigator.clipboard.writeText(content)` + toast success.

---

## 10. Future hook

Panel nhận `content: string` — Phase 2 swap `SpecPreviewPanel` inner từ markdown → `DashboardCanvas` without layout change.

---

## 11. Checklist step 08

- [ ] Panel shows spec.md after file_artifact
- [ ] Initial load from GET /artifacts
- [ ] Collapse/expand works + persists
- [ ] Empty state before spec exists
- [ ] Copy button works
- [ ] Mobile: preview accessible (tab or stack)
- [ ] memory.md not shown in preview

---

## 12. Cross-references

| File | Liên quan |
|------|-----------|
| [07-conversation-view.md](./07-conversation-view.md) | Chat left panel |
| [`Backend/agent/phase-1/10-checklist.md`](../../Backend/agent/phase-1/10-checklist.md) | DoD #6, #8 spec.md |
| [`02-ui-features-chat-agent.md`](../02-ui-features-chat-agent.md) §8 | Full canvas spec |
