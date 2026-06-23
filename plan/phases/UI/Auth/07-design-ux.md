# 07 — Design & UX Patterns

> Visual design, layout, accessibility, responsive, và error/toast patterns cho Auth slice.
>
> Align [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §9, §12, §14, §15 | [`01-project-structure-and-techstack.md`](../../../01-project-structure-and-techstack.md) §2.4

---

## 1. Visual direction

Auth pages là **first impression** của DashZen Studio — clean, professional, data-product aesthetic.

| Attribute | Guideline |
|-----------|-----------|
| Tone | Minimal, confident — không cluttered |
| Density | Spacious card form — 1 column |
| Brand | DashZen wordmark + subtle gradient accent (optional) |
| Dark mode | Support từ ngày 1 — `ThemeProvider` + CSS variables |
| Language | Vietnamese UI copy MVP — code/keys English |

---

## 2. Layout tokens

| Token | Value | Usage |
|-------|-------|-------|
| Card max-width | `28rem` (448px) | Auth card |
| Page padding | `1rem` mobile, `2rem` desktop | Outer |
| Card padding | `1.5rem` / `2rem` | Inner |
| Form gap | `1rem` between fields | `space-y-4` |
| Button height | `2.5rem` (40px) | Primary CTA |

### 2.1 Auth page wireframe

```
┌────────────────────────────────────────────────────────┐
│  bg: background (subtle mesh gradient optional)        │
│                                                        │
│              ┌─ DashZen ─┐                             │
│                                                        │
│         ╭──────────────────────────╮                   │
│         │  Đăng nhập               │                   │
│         │  Tiếp tục vào Studio      │                   │
│         │                          │                   │
│         │  [ email            ]    │                   │
│         │  [ password         ]    │                   │
│         │                          │                   │
│         │  [    Đăng nhập     ]    │  ← primary       │
│         │                          │                   │
│         │  Chưa có TK? Đăng ký     │  ← muted link    │
│         ╰──────────────────────────╯                   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 3. Component styling (shadcn)

| Element | Variant |
|---------|---------|
| Primary button | `default` — full width on mobile |
| Secondary link | `link` hoặc `ghost` |
| Destructive | Logout only |
| Input error | `border-destructive` + message `text-destructive text-sm` |
| Card | `shadow-sm` — không shadow quá nặng |

### 3.1 Focus & keyboard

- Tab order: logo (skip) → fields → submit → footer links
- Enter submit form khi focus trong input
- Visible focus ring (`ring-2 ring-ring`)

---

## 4. States & feedback

Align [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §9.

| State | Pattern |
|-------|---------|
| **Loading** | Button spinner + `disabled` inputs |
| **Success** | Toast short (3s) + navigate |
| **Error (form)** | Inline under field hoặc `FormError` banner top |
| **Error (global)** | Toast bottom-right |
| **Empty** | N/A auth forms |
| **Skeleton** | AuthGuard full-page — 3 pulse bars |

### 4.1 Toast messages (copy)

| Event | Toast |
|-------|-------|
| Register OK | "Kiểm tra email để lấy mã xác thực" |
| Verify OK | "Email đã được xác thực" |
| Resend OK | "Đã gửi mã mới" |
| Logout OK | (optional) "Đã đăng xuất" |
| Session expired | "Phiên hết hạn — vui lòng đăng nhập lại" |
| Rate limit | "Quá nhiều yêu cầu — thử lại sau {n}s" |

---

## 5. Error handling UX

### 5.1 Classification (Auth subset)

| Status | Auth UI |
|--------|---------|
| 400 validation | Inline `fields[]` |
| 401 login | Form banner — không toast |
| 403 email_not_verified | Alert trong login form |
| 409 email_exists | Inline email |
| 429 | Toast + disable CTA |
| 500 | Toast "Lỗi máy chủ — thử lại sau" |

### 5.2 Không làm

- Không hiện raw JSON error cho user
- Không expose stack trace
- Không differentiate "email không tồn tại" vs "sai password" (BE đã generic)

---

## 6. Accessibility (a11y)

Align §12 — Auth MVP baseline:

| Requirement | Implementation |
|-------------|----------------|
| Labels | Mọi input có `<Label htmlFor>` |
| Errors | `aria-describedby` link tới error id |
| Color contrast | WCAG AA — dùng theme tokens |
| Touch targets | Min 44×44px buttons mobile |
| Screen reader | Page `h1` unique per route |
| OTP | `autoComplete="one-time-code"` |

### 6.1 Form announcements

Live region cho submit errors:

```tsx
<div role="alert" aria-live="polite">{formError}</div>
```

---

## 7. Responsive

| Breakpoint | Auth layout |
|------------|-------------|
| `< 640px` | Card full bleed với `px-4`, button full width |
| `≥ 640px` | Centered card `max-w-md` |
| `≥ 1024px` | Optional split: illustration trái, form phải (Phase 2) |

**Mobile:** Không sidebar. Safe area `pb-safe` cho iOS home indicator.

---

## 8. Theme

| Mode | Background | Card |
|------|------------|------|
| Light | `bg-muted/30` | `bg-card` |
| Dark | `bg-background` | `bg-card border` |

Persist theme qua `themeStore` + `localStorage` — không liên quan auth session.

---

## 9. Motion (subtle)

| Interaction | Animation |
|-------------|-----------|
| Page enter | `fade-in` 150ms — optional |
| Error shake | Không — giữ professional |
| Loading | Spinner only |

Tránh animation phân tâm trên auth critical path.

---

## 10. Cross-links & legal (footer)

Auth card footer (optional MVP):

```
Đăng nhập · Đăng ký
```

Phase 2: Terms of Service, Privacy Policy links.

---

## 11. Profile & Settings visual

### 11.1 MVP (as-built)

| Page | Layout |
|------|--------|
| Settings | Card Session — `Sign out` destructive |
| Profile | Definition list: label / value rows (read-only) |

### 11.2 Phase 2 — Account management

> Vị trí button chi tiết: [10-account-management.md](./10-account-management.md) §3

| Page | Sections | Primary actions (vị trí) |
|------|----------|----------------------------|
| **Profile** | Header + profile card | `Edit profile` (header phải) → `Cancel` + `Save changes` |
| **Settings** | Profile link card | `Go to profile →` (card phải) |
| **Settings** | Security card | `Change password` → Dialog |
| **Settings** | Session card | `Sign out` (đã có) |
| **Settings** | Danger zone card | `Delete account` → Dialog (`border-destructive/30`) |

| Dialog | Footer buttons |
|--------|----------------|
| Change password | `Cancel` (ghost) · `Update password` (default) |
| Delete account | `Cancel` (ghost) · `Delete my account` (destructive, disabled until confirm) |

Dùng cùng app shell sidebar — nav `Profile` / `Settings` không chứa action buttons, chỉ điều hướng.

---

## 12. Design checklist (pre-ship)

- [ ] Light + dark mode readable
- [ ] Mobile 375px không overflow
- [ ] Keyboard-only login flow works
- [ ] Error states có text rõ ràng (VI)
- [ ] Loading không double-submit
- [ ] Logo/links có sufficient contrast
