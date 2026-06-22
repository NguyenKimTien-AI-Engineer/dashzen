# 03 — Frontend Integration (Next.js Studio)

> Coordination với [`UI/UX/phase-1-mvp-foundation.md`](../../UI/UX/phase-1-mvp-foundation.md) §3.1 — implement **sau** backend auth routes chạy được.
>
> **Không** lưu JWT vào localStorage — chỉ httpOnly cookies + `credentials: 'include'`.

---

## 1. Cấu trúc file

```
apps/studio/
├── middleware.ts                    # Route guard (edge)
├── app/
│   ├── (auth)/
│   │   ├── layout.tsx               # Guest layout (centered, no sidebar)
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── app/
│       └── layout.tsx               # Wrap AuthGuard + AppSidebar (later)
├── components/auth/
│   ├── AuthGuard.tsx                # Client session check
│   ├── LoginForm.tsx
│   └── RegisterForm.tsx
└── lib/
    ├── api/
    │   ├── client.ts                # fetchWithAuth + 401 interceptor
    │   └── auth.ts                  # login, register, logout, refresh, me
    └── stores/
        └── authStore.ts             # Zustand — user profile ephemeral (optional)
```

---

## 2. API client — bước ⑤⑥ chuẩn JWT

```typescript
// lib/api/client.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include", // ④ cookie auto-send
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (res.status === 401 && !path.includes("/auth/")) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return fetchWithAuth(path, options); // retry once
    }
    redirectToLogin();
    throw new SessionExpiredError();
  }

  return res;
}
```

```typescript
// lib/api/auth.ts

export async function login(email: string, password: string) { ... }
export async function register(email: string, password: string, displayName?: string) { ... }
export async function logout() { ... }
export async function refreshToken() { ... }  // POST /v1/auth/refresh
export async function getMe() { ... }         // GET /v1/auth/me
```

---

## 3. Login / Register forms

| Field | Validation (zod) |
|-------|------------------|
| email | valid email |
| password | min 8 chars |
| display_name | optional, register only |

**Login flow:**

1. User submit form
2. `POST /v1/auth/login` — cookies set by browser
3. `router.push(returnTo ?? "/app")`

**Register flow:**

1. `POST /v1/auth/register`
2. Auto-login (backend set cookies)
3. `router.push("/app")`

**Error display:** map `error.code` → inline field / toast (plan 02 §15.1 — 400 inline).

---

## 4. Next.js middleware — route guard

```typescript
// middleware.ts

const PUBLIC_PATHS = ["/login", "/register"];
const AUTH_PATHS = ["/login", "/register"];
const PROTECTED_PREFIX = "/app";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasAccessCookie = request.cookies.has("dashzen_access_token");

  // Guest-only: redirect if already logged in
  if (AUTH_PATHS.some((p) => pathname.startsWith(p)) && hasAccessCookie) {
    return NextResponse.redirect(new URL("/app", request.url));
  }

  // Protected: redirect if no cookie
  if (pathname.startsWith(PROTECTED_PREFIX) && !hasAccessCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("return_to", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/login", "/register"],
};
```

> Cookie presence ≠ valid token. API vẫn verify; middleware chỉ UX redirect sớm.

---

## 5. AuthGuard (client)

```typescript
// components/auth/AuthGuard.tsx

export function AuthGuard({ children }: { children: React.ReactNode }) {
  // Optional: call GET /v1/auth/me on mount
  // Loading → skeleton
  // 401 → redirect /login
  // Success → render children
}
```

Wrap trong `app/app/layout.tsx`:

```tsx
export default function AppLayout({ children }) {
  return (
    <AuthGuard>
      {/* Sidebar + main — Phase 1 later */}
      <main>{children}</main>
    </AuthGuard>
  );
}
```

---

## 6. Logout

1. `POST /v1/auth/logout` — server clear cookies
2. Clear `authStore` nếu có
3. `router.push("/login")`

Sidebar Settings → Logout button (Phase 1 shell).

---

## 7. SSE & Auth (quan trọng)

`TaskConnection` dùng `fetch` stream — **phải** `credentials: 'include'`.

| Case | Hành vi |
|------|---------|
| 401 khi mở stream | Stop stream, toast "Phiên hết hạn", redirect login |
| Không retry refresh trong SSE | User login lại, quay lại task |

```typescript
// task-connection.tsx — pattern
const res = await fetch(streamUrl, {
  method: "POST",
  credentials: "include",
  body: JSON.stringify(body),
});
if (res.status === 401) {
  dispatch({ type: "SESSION_EXPIRED" });
  return;
}
```

---

## 8. `return_to` query param

```
/login?return_to=/app/task/abc-123
```

Sau login thành công:

```typescript
const returnTo = searchParams.get("return_to");
router.push(returnTo?.startsWith("/app") ? returnTo : "/app");
```

Validate prefix — chỉ allow internal paths, chống open redirect.

---

## 9. Auth store (optional Zustand)

```typescript
// lib/stores/authStore.ts — UI ephemeral only

type AuthStore = {
  user: { id: string; email: string; displayName?: string } | null;
  setUser: (user) => void;
  clear: () => void;
};
```

Hydrate từ `GET /v1/auth/me` sau login / app mount — **không** lưu token.

---

## 10. Environment

```env
# apps/studio/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 11. Thứ tự implement FE

- [ ] `lib/api/client.ts` + `auth.ts`
- [ ] `LoginForm` + `login/page.tsx`
- [ ] `RegisterForm` + `register/page.tsx`
- [ ] `middleware.ts`
- [ ] `AuthGuard` + `app/app/layout.tsx`
- [ ] Logout action
- [ ] Manual test: login → `/app` → refresh page → vẫn logged in
- [ ] Manual test: expire access (giảm TTL dev) → auto refresh
