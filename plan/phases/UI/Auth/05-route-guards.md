# 05 — Route Guards & Session Protection

> Middleware (edge), AuthGuard (client), `return_to`, và auth trong SSE.
>
> Planner authoritative: [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §2.2

---

## 1. Hai lớp bảo vệ

| Lớp | Vị trí | Mục đích | Độ tin cậy |
|-----|--------|----------|------------|
| **Middleware** | `middleware.ts` (Edge) | Redirect UX sớm | Cookie **presence** only |
| **AuthGuard** | `(app)/layout.tsx` (Client) | Verify session + loading | `GET /auth/me` |
| **API** | FastAPI deps | Authoritative | JWT verify |

```
Request /app/*
  → middleware: có access cookie?
      No  → redirect /login?return_to=
      Yes → render layout
  → AuthGuard: GET /me OK?
      No  → redirect login (refresh đã fail trong client)
      Yes → render app
  → API calls: fetchWithAuth refresh on 401
```

---

## 2. Next.js middleware

```typescript
// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AUTH_ROUTES = ["/login", "/register", "/verify-email"];
const PROTECTED_PREFIX = "/app";
const ACCESS_COOKIE = "dashzen_access_token"; // mirror BE config name

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasAccess = request.cookies.has(ACCESS_COOKIE);

  const isAuthRoute = AUTH_ROUTES.some(
    (r) => pathname === r || pathname.startsWith(`${r}/`),
  );
  const isProtected = pathname.startsWith(PROTECTED_PREFIX);

  if (isAuthRoute && hasAccess) {
    return NextResponse.redirect(new URL("/app", request.url));
  }

  if (isProtected && !hasAccess) {
    const login = new URL("/login", request.url);
    login.searchParams.set("return_to", pathname);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/login", "/register", "/verify-email"],
};
```

### 2.1 Lưu ý

- Cookie name đọc từ env `NEXT_PUBLIC_ACCESS_COOKIE_NAME` (optional) — default `dashzen_access_token`
- Middleware **không** gọi API — tránh latency edge
- Expired cookie vẫn pass middleware → AuthGuard/API bắt

---

## 3. AuthGuard implementation

```typescript
"use client";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data, isLoading, isError } = useMe();

  useEffect(() => {
    if (!isLoading && (isError || !data)) {
      const login = `/login?return_to=${encodeURIComponent(pathname)}`;
      router.replace(login);
    }
  }, [isLoading, isError, data, pathname, router]);

  if (isLoading) return <AppShellSkeleton />;
  if (isError || !data) return null;

  return <>{children}</>;
}
```

### 3.1 useMe hook

```typescript
export function useMe() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: getMe,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}
```

`getMe` dùng `fetchWithAuth` — tự refresh nếu access expired.

---

## 4. `return_to` — open redirect prevention

```typescript
export function safeReturnTo(raw: string | null): string {
  if (!raw) return "/app";
  // Chỉ internal app paths
  if (!raw.startsWith("/app")) return "/app";
  if (raw.startsWith("//")) return "/app";
  return raw;
}
```

Áp dụng sau login success và khi đọc `searchParams` trên login page.

---

## 5. Guest route behavior

| Route | Logged in (has cookie) | Action |
|-------|------------------------|--------|
| `/login` | Yes | → `/app` |
| `/register` | Yes | → `/app` |
| `/verify-email` | Yes | → `/app` (đã verify + session) |

Edge case: user có cookie nhưng `email_not_verified` không xảy ra ở FE nếu login blocked — cookie chỉ set sau login thành công.

---

## 6. SSE & streaming auth (forward reference)

Khi UX Phase 1 implement `TaskConnection`:

| Case | Hành vi |
|------|---------|
| Stream `fetch` | `credentials: 'include'` bắt buộc |
| 401 khi mở stream | **Không** silent refresh trong stream |
| UX | Dispatch `SESSION_EXPIRED` → toast → `router.push(/login?return_to=...)` |

```typescript
const res = await fetch(`${API_URL}/v1/tasks/${id}/stream`, {
  method: "POST",
  credentials: "include",
  body: JSON.stringify(payload),
});

if (res.status === 401) {
  toast({ variant: "error", title: "Phiên đăng nhập hết hạn" });
  router.push(`/login?return_to=${encodeURIComponent(pathname)}`);
  return;
}
```

Auth slice: document pattern — implement trong `modules/task` Phase 1 UX.

---

## 7. Logout & guard reset

```typescript
export async function logout() {
  await logoutApi();           // POST /auth/logout
  queryClient.removeQueries({ queryKey: ["auth"] });
  authStore.getState().clear();
  router.push("/login");
}
```

Middleware thấy cookie cleared ở request tiếp theo → protected routes redirect.

---

## 8. 401 global handling (non-auth pages)

`fetchWithAuth` centralizes:

1. Try refresh once
2. Fail → `redirectToLogin()` — preserve `window.location.pathname` as `return_to`
3. Toast: "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại."

`redirectToLogin` dùng `window.location.href` (full navigation) để reset React state sạch.

---

## 9. Matcher expansion (future)

| Route | Phase |
|-------|-------|
| `/app/*` | MVP |
| `/onboarding` | Phase 2 |
| `/` marketing | Public — không trong matcher |

Giữ matcher **hẹp** — chỉ routes cần guard.
