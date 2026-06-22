# 04 — API Contracts (Auth)

> OpenAPI-style reference cho Auth endpoints. **As-built** sau security hardening (2026-06-22).

**Base URL:** `{API_URL}/v1`  
**Auth transport:** httpOnly cookies (primary) | `Authorization: Bearer <access_token>` (fallback)

---

## 1. POST `/auth/register`

Tạo user mới và đăng nhập (set cookies).

> **Planned change:** Khi có email verification, response sẽ **không** set cookies — xem [06-email-verification.md](./06-email-verification.md).

### Request

```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "display_name": "Kim Tien"
}
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| email | string | ✓ | email format |
| password | string | ✓ | min 8, 1 letter, 1 digit |
| display_name | string | | max 100; `""` → null |

### Response `201 Created`

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "Kim Tien"
  }
}
```

**Set-Cookie:** `dashzen_access_token`, `dashzen_refresh_token`

**Rate limit:** 10 requests/minute per IP

### Errors

| Status | code |
|--------|------|
| 400 | `validation_error` |
| 409 | `email_exists` |
| 429 | rate limit exceeded |

---

## 2. POST `/auth/login`

### Request

```json
{
  "email": "user@example.com",
  "password": "securepass123"
}
```

### Response `200 OK`

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "display_name": "Kim Tien"
  }
}
```

**Set-Cookie:** access + refresh

**Rate limit:** 5 requests/minute per IP

### Errors

| Status | code |
|--------|------|
| 401 | `invalid_credentials` |
| 429 | rate limit exceeded |

> Inactive account cũng trả `401 invalid_credentials` (không lộ account tồn tại).

---

## 3. POST `/auth/refresh`

Silent refresh — chỉ cần refresh cookie (không body).

### Request

- Cookie: `dashzen_refresh_token`
- Body: `{}` hoặc empty

### Response `200 OK`

```json
{
  "ok": true
}
```

**Set-Cookie:** new access + refresh (rotation — old `jti` revoked)

**Rate limit:** 3 requests/minute per IP

### Errors

| Status | code |
|--------|------|
| 401 | `token_expired` |
| 401 | `token_invalid` |
| 429 | rate limit exceeded |

---

## 4. POST `/auth/logout`

### Request

- Cookie: `dashzen_refresh_token` (để revoke server-side)

### Response `200 OK`

```json
{
  "ok": true
}
```

**Server:** revoke refresh `jti` in DB  
**Set-Cookie:** clear both (Max-Age=0)

---

## 5. GET `/auth/me`

Protected — cần access token.

### Response `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "display_name": "Kim Tien",
  "created_at": "2026-06-22T00:00:00Z"
}
```

### Errors

| Status | code |
|--------|------|
| 401 | `token_expired` / `token_invalid` / `token_type_mismatch` |
| 403 | `user_inactive` |

---

## 6. Cookie specification

### `dashzen_access_token`

```
Set-Cookie: dashzen_access_token=<jwt>; HttpOnly; Path=/; SameSite=Lax; Max-Age=900
```

> Max-Age=900 = **15 phút** (as-built).

### `dashzen_refresh_token`

```
Set-Cookie: dashzen_refresh_token=<jwt>; HttpOnly; Path=/v1/auth; SameSite=Lax; Max-Age=604800
```

**Production:** `Secure` flag (auto khi `APP_ENV != development`).

---

## 7. Bearer fallback

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

Dùng cho: curl, API testing, future mobile client. Studio MVP dùng cookies.

---

## 8. Protected endpoints (cần auth)

Tất cả endpoints sau yêu cầu valid access token:

| Method | Path |
|--------|------|
| GET | `/v1/auth/me` |
| POST | `/v1/tasks` |
| GET | `/v1/tasks` |
| GET/PATCH/DELETE | `/v1/tasks/{id}` |
| GET | `/v1/tasks/{id}/messages` |
| GET | `/v1/tasks/{id}/artifacts` |
| POST | `/v1/tasks/{id}/stream` |
| POST | `/v1/tasks/{id}/stop` |
| POST | `/v1/tasks/{id}/upload` |
| POST | `/v1/tasks/{id}/gates/*` |
| POST | `/v1/tasks/{id}/compact` |

**Public (no auth):**

| Method | Path |
|--------|------|
| POST | `/v1/auth/login` |
| POST | `/v1/auth/register` |
| POST | `/v1/auth/refresh` |
| POST | `/v1/auth/logout` |
| GET | `/health` |

---

## 9. Planned endpoints (email verification)

Xem [06-email-verification.md](./06-email-verification.md):

| Method | Path |
|--------|------|
| POST | `/v1/auth/verify-email` |
| POST | `/v1/auth/resend-verification` |

---

## 10. Error envelope (shared)

```json
{
  "error": {
    "code": "token_expired",
    "message": "Your session has expired. Please sign in again."
  }
}
```

Validation errors include `fields` array:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Password must be at least 8 characters.",
    "fields": [
      { "field": "password", "code": "password_too_short", "message": "..." }
    ]
  }
}
```

Frontend map `code` → toast / redirect / inline error.
