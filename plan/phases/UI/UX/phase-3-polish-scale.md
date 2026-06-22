# Phase 3 — Polish & Scale

> **Mục tiêu:** Tính năng discovery, personalization, export/share — nâng DashZen từ "dùng được" lên "dùng thích".
>
> **Nguồn:** [`02-ui-features-chat-agent.md`](../../02-ui-features-chat-agent.md) §19 Phase 3, §8.2, §10.7, §12.1, §20
>
> **Ưu tiên:** P2–P3 | **Phụ thuộc:** Phase 1 + Phase 2 hoàn thành

---

## 1. Scope overview

Phase 3 là **nice-to-have** — không block MVP hay core UX. Tập trung:

- **Output:** Export, share, print dashboard
- **Personalization:** User prefs, custom instructions, defaults
- **Discovery:** Command palette, template gallery, onboarding tour
- **Scale:** i18n, multi-user gates, debug tooling

### Không thuộc Phase 3 (out of scope)

- `spawn_task` multi-task — optional, chưa plan chi tiết
- Auth migration better-auth — documented plan-01 §10.11, MVP = JWT

---

## 2. Deliverables checklist

### 2.1 Export & share dashboard (§8.2)

- [ ] Toolbar full-screen preview: **Export** button
- [ ] Export formats: PNG snapshot, PDF (phase tùy backend)
- [ ] Share link — generate read-only URL (nếu backend hỗ trợ)
- [ ] **Print-friendly CSS** cho full-screen preview
- [ ] Copy embed code (optional)

### 2.2 User preferences (§10.7)

| Pref | Storage | UI |
|------|---------|-----|
| `default_mode` | Account + localStorage per task | Ask/Auto toggle default |
| `default_thinking` | Account | Settings toggle |
| `custom_instructions` | Account | Settings textarea → `# USER` block |
| `language` | Account | Settings dropdown |

- [ ] Settings page: section User Preferences
- [ ] Sync account prefs ↔ localStorage fallback offline
- [ ] Apply `custom_instructions` vào prompt context khi tạo task mới

### 2.3 Internationalization (i18n)

- [ ] VI / EN language toggle trong Settings
- [ ] Extract UI strings → i18n keys (sidebar, toast, empty states, ActionCard)
- [ ] Date/time relative format theo locale
- [ ] Không i18n agent-generated content (giữ nguyên ngôn ngữ user prompt)

### 2.4 Discovery & onboarding

- [ ] **Command palette** `Cmd+K` — search tasks, navigate routes, quick actions
- [ ] **Template gallery** — "From Template" chip → modal chọn template
- [ ] **Onboarding tour** — interactive walkthrough lần đầu login
  - Step 1: New Dashboard
  - Step 2: Ask/Auto mode
  - Step 3: Canvas preview
  - Step 4: Approve tool
- [ ] **Favorite / bookmark** dashboard trong sidebar recents

### 2.5 Full-screen preview nâng cao (§8.2)

- [ ] Toolbar: **View code** — hiện spec.md / widget config (read-only)
- [ ] Continue in chat — navigate `/app/task/{taskId}` (đã có Phase 1, polish UX)
- [ ] Breadcrumb: Task title → Dashboard preview

### 2.6 Multi-user & access (nếu cần)

- [ ] Invite gate / email verification flow
- [ ] Share dashboard với quyền view/edit
- [ ] Profile page polish — avatar, email, change password

### 2.7 Developer & debug tooling

- [ ] **Debug trace panel** — SSE event log, reducer state snapshot (dev mode only)
- [ ] Toggle trong Settings → "Developer mode"
- [ ] Copy debug bundle cho support

### 2.8 Sidebar & search nâng cao

- [ ] `Cmd+K` integrate với sidebar search
- [ ] Duplicate task từ context menu (đã list Phase 2, polish UX)
- [ ] Sort recents: recent / alphabetical / favorites first
- [ ] Archive / hide task

### 2.9 Accessibility polish (§12)

- [ ] Full keyboard nav audit WCAG 2.1 AA
- [ ] Screen reader test: streaming, ActionCard, canvas
- [ ] High contrast mode support (optional)
- [ ] `prefers-reduced-motion` audit toàn app

### 2.10 Auth evolution (optional)

- [ ] Evaluate migration JWT → better-auth (plan-01 §10.11)
- [ ] OAuth providers (Google, GitHub) nếu product yêu cầu
- [ ] Session management UI — active devices, revoke

---

## 3. Definition of done

Phase 3 hoàn thành khi (tùy product priority — không cần tất cả):

1. User export/share dashboard từ full-screen preview
2. User cấu hình default Ask/Auto, custom instructions, language
3. New user hoàn thành onboarding tour
4. Power user dùng Cmd+K navigate nhanh
5. Template gallery giúp bắt đầu nhanh hơn blank prompt
6. (Optional) Debug panel hỗ trợ troubleshoot SSE issues

---

## 4. Ưu tiên triển khai trong Phase 3

Nếu resource hạn chế, thứ tự đề xuất:

| # | Feature | Impact | Effort |
|---|---------|--------|--------|
| 1 | User prefs (default_mode, custom_instructions) | Cao | Trung bình |
| 2 | Export PNG/PDF | Cao | Trung bình |
| 3 | Template gallery | Cao | Cao |
| 4 | i18n VI/EN | Trung bình | Cao |
| 5 | Command palette Cmd+K | Trung bình | Trung bình |
| 6 | Onboarding tour | Trung bình | Trung bình |
| 7 | Debug trace panel | Thấp (dev) | Thấp |
| 8 | Print-friendly CSS | Thấp | Thấp |
| 9 | Favorite/bookmark | Thấp | Thấp |
| 10 | Multi-user invite | Tùy product | Cao |

---

## 5. Cross-references

| Gap (§20) | Phase 3 action |
|-----------|----------------|
| `spawn_task` multi-task | Out of scope — optional |
| Auth better-auth vs JWT | Evaluate migration |
| Export / share | §2.1 |
| User prefs | §2.2 |
| i18n | §2.3 |
| Command palette | §2.4 |
| Template gallery | §2.4 |
| Debug trace | §2.7 |
