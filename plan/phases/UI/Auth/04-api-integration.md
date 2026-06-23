# 04 — API Integration

> Frontend integration với Auth API — client, types, error mapping.
>
> **Backend reference (authoritative payloads):** [Backend 04-api-contracts.md](../../Backend/auth/04-api-contracts.md)

**Base URL:** `${NEXT_PUBLIC_API_URL}/v1`  
**Transport:** `credentials: 'include'` — httpOnly cookies

---

## 1. `lib/api/client.ts`

### 1.1 Core fetch

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL!;

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public body: ApiErrorBody["error"],
  ) {
    super(body.message);
  }
}

export class SessionExpiredError extends Error {}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
        });
        return res.ok;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

export async function fetchWithAuth(
  path: string,
  options: RequestInit = {},
  retried = false,
): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (res.status === 401 && !path.startsWith("/auth/") && !retried) {
    const refreshed = await tryRefreshToken();
    if (refreshed) return fetchWithAuth(path, options, true);
    redirectToLogin();
    throw new SessionExpiredError();
  }

  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After");
    throw new RateLimitError(retryAfter);
  }

  if (!res.ok) {
    const body = (await res.json()) as ApiErrorBody;
    throw new ApiError(res.status, body.error.code, body.error);
  }

  return res;
}
```

### 1.2 Public fetch (auth endpoints)

Auth routes **không** qua refresh interceptor khi 401 expected:

```typescript
export async function fetchPublic(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!res.ok) {
    const body = (await res.json()) as ApiErrorBody;
    throw new ApiError(res.status, body.error.code, body.error);
  }
  return res;
}
```

---

## 2. `lib/api/auth.ts`

| Function | Method | Path | Response |
|----------|--------|------|----------|
| `register` | POST | `/auth/register` | `RegisterResponse` |
| `verifyEmail` | POST | `/auth/verify-email` | `OkResponse` |
| `resendVerification` | POST | `/auth/resend-verification` | `OkResponse` |
| `login` | POST | `/auth/login` | `AuthUserResponse` |
| `logout` | POST | `/auth/logout` | `OkResponse` |
| `refreshToken` | POST | `/auth/refresh` | `OkResponse` |
| `getMe` | GET | `/auth/me` | `User` |

**Phase 2 (planned)** — xem [10-account-management.md](./10-account-management.md) §5–6:

| Function | Method | Path | Response |
|----------|--------|------|----------|
| `updateProfile` | PATCH | `/auth/me` | `User` |
| `changePassword` | POST | `/auth/change-password` | `OkResponse` |
| `deleteAccount` | DELETE | `/auth/me` | `OkResponse` + clear cookies |

```typescript
export async function login(email: string, password: string) {
  const res = await fetchPublic("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  return (await res.json()) as AuthUserResponse;
}

export async function register(
  email: string,
  password: string,
  displayName?: string,
) {
  const res = await fetchPublic("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      display_name: displayName ?? null,
    }),
  });
  return (await res.json()) as RegisterResponse;
}

export async function verifyEmail(email: string, code: string) {
  const res = await fetchPublic("/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ email, code }),
  });
  return (await res.json()) as OkResponse;
}
```

---

## 3. Error code → UI mapping

Align [`02-ui-features-chat-agent.md`](../../../02-ui-features-chat-agent.md) §15.

### 3.1 Auth-specific codes

| HTTP | `code` | UI handling |
|------|--------|-------------|
| 400 | `validation_error` | Map `fields[]` → inline inputs |
| 401 | `invalid_credentials` | Form banner login |
| 401 | `token_expired` / `token_invalid` | Redirect login (session) |
| 403 | `email_not_verified` | Alert + link verify page |
| 403 | `user_inactive` | Toast error |
| 409 | `email_exists` | Inline email field register |
| 400 | `invalid_code` | OTP field error |
| 400 | `too_many_attempts` | Banner + force resend |
| 400 | `already_verified` | Redirect login với message |
| 429 | (rate limit) | Toast + cooldown UI |

### 3.2 `parseFieldErrors` helper

```typescript
export function mapFieldErrors(
  fields: ApiErrorBody["error"]["fields"],
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const f of fields ?? []) {
    out[f.field] = f.message;
  }
  return out;
}
```

---

## 4. Request/response contracts (FE summary)

### POST `/auth/register`

**Request:**
```json
{ "email": "...", "password": "...", "display_name": "..." }
```

**Response `201`:**
```json
{
  "user": { "id": "...", "email": "...", "display_name": "...", "email_verified": false },
  "requires_verification": true
}
```

**No Set-Cookie** — FE không expect cookies.

### POST `/auth/login`

**Response `200`:** `{ "user": { ... } }` + Set-Cookie

### POST `/auth/verify-email`

```json
{ "email": "user@example.com", "code": "123456" }
```

### POST `/auth/resend-verification`

```json
{ "email": "user@example.com" }
```

### GET `/auth/me`

```json
{
  "id": "...",
  "email": "...",
  "display_name": "...",
  "email_verified": true,
  "created_at": "..."
}
```

### Phase 2 endpoints (planned)

| Endpoint | Body summary | Notes |
|----------|--------------|-------|
| `PATCH /auth/me` | `{ "display_name": "..." }` | Invalidate `['auth','me']` |
| `POST /auth/change-password` | `{ "current_password", "new_password" }` | Session giữ nguyên |
| `DELETE /auth/me` | `{ "password", "confirmation": "DELETE" }` | Clear cookies server-side |

Chi tiết errors & UI mapping: [10-account-management.md](./10-account-management.md).

---

## 5. Cookies (FE awareness only)

| Cookie | Middleware check | API |
|--------|------------------|-----|
| `dashzen_access_token` | `request.cookies.has(...)` | Auto-sent `Path=/` |
| `dashzen_refresh_token` | Optional | Auto-sent `Path=/v1/auth` |

FE **không đọc** giá trị cookie — chỉ rely browser + `credentials: 'include'`.

---

## 6. CORS requirements

| Header (request) | Value |
|------------------|-------|
| `Origin` | `http://localhost:3000` |
| `Credentials` | include |

Backend `CORS_ORIGINS` phải whitelist Studio origin.

---

## 7. Testing API layer (dev)

```bash
# Health
curl -s http://localhost:8000/health

# Register (no cookie)
curl -s -X POST http://localhost:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"securepass1"}'
```

Studio integration tests (Phase 2): MSW mock hoặc Playwright against real API.

---

## 8. Rate limits (awareness)

| Endpoint | Limit (as-built) | FE UX |
|----------|------------------|-------|
| login | 5/min/IP | Toast + disable |
| register | 10/min/IP | Toast |
| refresh | 3/min/IP | Silent — avoid refresh storm |
| verify-email | per settings | Inline error |
| resend | 3/hour/email | Countdown button |

Parse `Retry-After` header khi 429.
