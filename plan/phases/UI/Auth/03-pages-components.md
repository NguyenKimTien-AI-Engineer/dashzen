# 03 — Pages & Components

> Đặc tả UI pages, forms, và component tree cho Auth slice.
>
> Design visual: [07-design-ux.md](./07-design-ux.md) | API: [04-api-integration.md](./04-api-integration.md)

---

## 1. Route map

| Route | Page file | Layout | Auth |
|-------|-----------|--------|------|
| `/login` | `(auth)/login/page.tsx` | `AuthLayout` | Guest |
| `/register` | `(auth)/register/page.tsx` | `AuthLayout` | Guest |
| `/verify-email` | `(auth)/verify-email/page.tsx` | `AuthLayout` | Guest |
| `/app` | `(app)/page.tsx` | `AuthGuard` + shell | Protected |
| `/app/settings` | `(app)/settings/page.tsx` | Protected | Logout CTA |
| `/app/profile` | `(app)/profile/page.tsx` | Protected | User info |

---

## 2. AuthLayout

Layout chung cho mọi trang `(auth)/`:

```
┌─────────────────────────────────────────┐
│              [DashZen logo]             │
│                                         │
│         ┌─────────────────────┐         │
│         │   Card (max-w-md)   │         │
│         │   {children}        │         │
│         └─────────────────────┘         │
│                                         │
│     Link: Đăng nhập ↔ Đăng ký          │
│                                         │
└─────────────────────────────────────────┘
```

| Prop / slot | Mô tả |
|-------------|-------|
| `title` | H1 trong card — "Đăng nhập", "Tạo tài khoản", ... |
| `description` | Subtitle optional |
| `children` | Form content |
| `footer` | Cross-links giữa login/register |

**Responsive:** Card full-width padding trên mobile (`px-4`), centered `max-w-md` desktop.

---

## 3. LoginForm

### 3.1 Fields

| Field | Component | Validation (zod) |
|-------|-----------|------------------|
| email | `Input type="email"` | `z.string().email()` |
| password | `Input type="password"` | `min(1)` — server validates strength |

### 3.2 States

| State | UI |
|-------|-----|
| `idle` | Submit enabled khi form valid |
| `submitting` | Button loading, inputs disabled |
| `error` | `FormError` banner hoặc field-level |

### 3.3 Actions

- **Submit** → `useAuth().login()` → success navigate
- **Link** "Chưa có tài khoản?" → `/register`
- **Banner** khi `?verified=1` — success alert dismissible

### 3.4 return_to

Đọc `searchParams.return_to` — chỉ allow paths bắt đầu `/app`:

```typescript
function safeReturnTo(value: string | null): string {
  if (value?.startsWith("/app")) return value;
  return "/app";
}
```

---

## 4. RegisterForm

### 4.1 Fields

| Field | Required | Validation |
|-------|----------|------------|
| email | ✓ | email format |
| password | ✓ | min 8, 1 letter, 1 digit (mirror BE) |
| display_name | | max 100, optional |

**Password hint:** Text nhỏ dưới field — "Ít nhất 8 ký tự, gồm chữ và số".

### 4.2 Success flow

```typescript
const res = await register(data);
// res.requires_verification === true
router.push(`/verify-email?email=${encodeURIComponent(res.user.email)}`);
```

Không gọi `login` tự động. Toast: "Chúng tôi đã gửi mã xác thực đến email của bạn."

---

## 5. VerifyEmailForm

### 5.1 Layout

```
Xác thực email
Chúng tôi đã gửi mã 6 số đến user@example.com

[ OTP input: □ □ □ □ □ □ ]  hoặc single input

[ Xác nhận ]  (disabled until 6 digits)

Gửi lại mã (60s)     ← countdown button
Quay lại đăng nhập
```

### 5.2 OtpInput component

| Behavior | Spec |
|----------|------|
| 6 ô riêng hoặc 1 input `inputMode="numeric"` | MVP: 1 input `maxLength=6` pattern `\d{6}` |
| Paste support | Auto-fill 6 digits từ clipboard |
| Auto-advance | Optional Phase 1.1 — 6 ô |
| `onComplete` | Auto-submit khi đủ 6 (optional) |

### 5.3 Email source

Priority: `searchParams.email` → fallback input email (nếu user vào trực tiếp `/verify-email`).

### 5.4 Resend button

- Local state `cooldownSeconds` — start 60s sau click
- Disabled khi `cooldownSeconds > 0` — label `Gửi lại (${s}s)`
- Server 429 → toast, sync cooldown từ `Retry-After` header nếu có

### 5.5 Success

→ `router.push(/login?verified=1&email=...)`

---

## 6. AuthGuard

Client-side guard trong `(app)/layout.tsx`:

| Phase | UI |
|-------|-----|
| Loading | Full-page skeleton hoặc spinner centered |
| Unauthenticated | `redirect('/login?return_to=' + pathname)` |
| Authenticated | Render `children` |

Dùng `useMe()` — `isLoading`, `isError`, `data`.

> Middleware đã redirect sớm nếu không có cookie — AuthGuard xử lý cookie invalid/expired.

---

## 7. Settings & Profile (MVP minimal)

### 7.1 `/app/settings`

| Element | Action |
|---------|--------|
| "Đăng xuất" button destructive/outline | `logout()` |
| Link profile | `/app/profile` |

### 7.2 `/app/profile`

| Field | Source |
|-------|--------|
| Email | `user.email` |
| Display name | `user.display_name` hoặc "—" |
| Verified badge | `user.email_verified` ✓/✗ |
| Member since | `created_at` formatted |

Read-only MVP — không edit form.

> **Phase 2:** Profile CRUD, change password, delete account — vị trí button & flows: [10-account-management.md](./10-account-management.md) §3.

---

## 8. Component dependency (shadcn)

| Component | Dùng ở |
|-----------|--------|
| `Button` | Submit, resend, logout |
| `Input` | email, password, OTP |
| `Label` | Form labels |
| `Card`, `CardHeader`, `CardContent` | AuthLayout |
| `Form` (shadcn form) | react-hook-form bridge |
| `Alert` | verified banner, email_not_verified |
| `Toast` | Global errors/success |

---

## 9. Page metadata

```typescript
// login/page.tsx
export const metadata = {
  title: "Đăng nhập — DashZen",
  description: "Đăng nhập vào DashZen Studio",
};
```

Auth pages: `robots: noindex` (optional).

---

## 10. Placeholder `/app` home

Cho đến khi UX Phase 1 có Task module:

```
/app → centered welcome
  "Xin chào, {displayName}"
  "Task chat sẽ có ở phase tiếp theo"
  [Đi tới Cài đặt]
```

Đủ để verify AuthGuard + session hoạt động end-to-end.
