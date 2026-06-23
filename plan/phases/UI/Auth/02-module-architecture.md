# 02 — Module Architecture (Studio Auth)

> Cấu trúc code Auth UI — ranh giới module, state, và quy ước import.
>
> Align [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §3.1, §3.2 — **Auth tách khỏi `modules/task`**.

---

## 1. Nguyên tắc

| Nguyên tắc | Ý nghĩa |
|------------|---------|
| **Auth ≠ Chat** | Không đưa auth state vào `task-reducer` |
| **No token in JS** | Không localStorage/sessionStorage cho JWT |
| **Thin pages** | `page.tsx` compose components + hooks — logic trong module |
| **API qua lib** | Mọi `fetch` auth đi qua `lib/api/auth.ts` hoặc `client.ts` |
| **Zustand ephemeral** | User profile cache UI — TanStack Query là source CRUD |

---

## 2. Cấu trúc file (target)

```
apps/studio/
├── middleware.ts                         # Edge route guard
│
├── app/
│   ├── layout.tsx                        # Root: QueryClient, Theme, Toaster
│   ├── (auth)/
│   │   ├── layout.tsx                    # Centered card layout, no sidebar
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   └── verify-email/page.tsx
│   └── (app)/
│       ├── layout.tsx                    # AuthGuard + AppSidebar (Phase 1 UX)
│       ├── page.tsx                      # Home — placeholder until Task module
│       ├── settings/page.tsx             # Logout, change password, delete (Phase 2)
│       └── profile/page.tsx              # Read-only MVP → edit display_name (Phase 2)
│
├── modules/auth/
│   ├── components/
│   │   ├── AuthLayout.tsx                # Logo, card wrapper, footer links
│   │   ├── LoginForm.tsx
│   │   ├── RegisterForm.tsx
│   │   ├── VerifyEmailForm.tsx
│   │   ├── OtpInput.tsx                  # 6-digit input component
│   │   ├── AuthGuard.tsx
│   │   ├── ProfileEditForm.tsx           # Phase 2
│   │   ├── ChangePasswordDialog.tsx      # Phase 2
│   │   └── DeleteAccountDialog.tsx       # Phase 2
│   ├── hooks/
│   │   ├── useAuth.ts                    # login, logout, register wrappers
│   │   ├── useMe.ts                      # TanStack Query GET /auth/me
│   │   ├── useVerifyEmail.ts
│   │   ├── useUpdateProfile.ts           # Phase 2
│   │   ├── useChangePassword.ts          # Phase 2
│   │   └── useDeleteAccount.ts           # Phase 2
│   ├── schemas/
│   │   ├── login.schema.ts               # zod
│   │   ├── register.schema.ts
│   │   ├── verify-email.schema.ts
│   │   ├── profile.schema.ts             # Phase 2
│   │   ├── change-password.schema.ts     # Phase 2
│   │   └── delete-account.schema.ts      # Phase 2
│   └── types/
│       └── auth.ts                       # User, ApiError mirrors
│
├── components/
│   ├── ui/                               # shadcn
│   └── shared/
│       ├── ToastContainer.tsx
│       └── FormError.tsx                 # Map API field errors
│
└── lib/
    ├── api/
    │   ├── client.ts                     # fetchWithAuth, ApiError, refresh
    │   ├── auth.ts                       # login, register, verify, me, ...
    │   └── errors.ts                     # parseErrorBody, code constants
    └── stores/
        ├── authStore.ts                  # optional: user snapshot
        └── toastStore.ts
```

---

## 3. State management

| Concern | Công nghệ | Owner |
|---------|-----------|-------|
| Form local state | `react-hook-form` | Form component |
| User profile (server) | TanStack Query `['auth', 'me']` | `useMe` hook |
| User snapshot (UI) | Zustand `authStore` (optional) | Hydrate từ `useMe` / sau login |
| Toast notifications | Zustand `toastStore` | Global |
| Route protection | `middleware.ts` + `AuthGuard` | Edge + client |
| Session refresh | `fetchWithAuth` interceptor | `lib/api/client.ts` |

### 3.1 authStore (optional)

```typescript
type AuthStore = {
  user: User | null;
  setUser: (user: User | null) => void;
  clear: () => void;
};
```

- Hydrate sau `login` success hoặc `useMe` success
- Clear sau `logout` hoặc session expired
- **Không** lưu token, **không** persist localStorage

### 3.2 TanStack Query keys

| Key | Query fn | staleTime |
|-----|----------|-----------|
| `['auth', 'me']` | `GET /v1/auth/me` | 5 phút |
| — invalidate on logout | `queryClient.clear()` hoặc remove `['auth']` | — |

---

## 4. Ranh giới import

```
app/(auth)/*     → modules/auth/*, components/ui, lib/api
app/(app)/*      → modules/auth/AuthGuard, modules/task/* (later), lib/api
modules/auth/*   → lib/api, components/ui — KHÔNG import modules/task
modules/task/*   → lib/api/client (fetchWithAuth) — KHÔNG import auth forms
lib/api/*        → không import React components
```

---

## 5. Providers (root layout)

```tsx
// app/layout.tsx — thứ tự đề xuất
<QueryClientProvider>
  <ThemeProvider>
    {children}
    <ToastContainer />
  </ThemeProvider>
</QueryClientProvider>
```

`AuthGuard` **không** đặt ở root — chỉ wrap `(app)/layout.tsx`.

---

## 6. Types mirror (FE)

```typescript
// modules/auth/types/auth.ts

export type User = {
  id: string;
  email: string;
  display_name: string | null;
  email_verified: boolean;
  created_at: string | null;
};

export type RegisterResponse = {
  user: User;
  requires_verification: boolean;
};

export type AuthUserResponse = {
  user: User;
};

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    fields?: Array<{ field: string; code: string; message: string }>;
  };
};
```

Giữ sync với `packages/core/src/core/schemas/auth.py`.

---

## 7. Tách khỏi UX Phase 1

| Auth Slice (file này) | UX Phase 1 (sau) |
|-----------------------|------------------|
| `(auth)/*` pages | `(app)/task/*` |
| `modules/auth/` | `modules/task/` |
| `AuthGuard` | `AppSidebar`, `TaskContext` |
| `lib/api/auth.ts` | `lib/api/tasks.ts`, `gates.ts` |

Auth slice **ship độc lập** khi: login/register/verify/guard pass checklist [08](./08-checklist.md) — chưa cần chat UI.

---

## 8. Thứ tự scaffold

1. `lib/api/client.ts` + `errors.ts`
2. `lib/api/auth.ts`
3. `modules/auth/schemas/*`
4. `modules/auth/components/AuthLayout.tsx`
5. `LoginForm` → `login/page.tsx`
6. `RegisterForm` → `register/page.tsx`
7. `VerifyEmailForm` + `OtpInput`
8. `AuthGuard` + `(app)/layout.tsx`
9. `middleware.ts`
