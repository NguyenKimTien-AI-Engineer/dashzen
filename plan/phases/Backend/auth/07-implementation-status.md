# 07 — Implementation Status (As-Built)

> Ghi nhận trạng thái code **đã implement** sau security review & hardening (2026-06-22).
>
> Dùng làm reference khi đối chiếu plan vs thực tế.

---

## 1. Cấu trúc file thực tế

```
packages/core/src/core/
├── auth/
│   ├── cookies.py              # set/clear cookies (cookie_secure_resolved)
│   ├── jwt.py                  # HS256 + RS256; create_refresh_token → (token, jti)
│   ├── password.py             # bcrypt cost 12
│   └── validation.py           # password strength rules
├── config.py                   # AppEnv enum, rate limit, JWT settings
├── exceptions.py               # AuthError hierarchy
└── schemas/
    ├── auth.py                 # PydanticCustomError for password validation
    └── validation.py           # format_validation_errors (structured)

packages/db/src/db/
├── models/
│   ├── user.py                 # + last_login_at
│   └── refresh_token.py        # jti PK, user_id FK, revoked, expires_at
├── repositories/
│   ├── user.py                 # get_by_email, create, update_last_login
│   └── refresh_token.py        # store, get, revoke
├── services/
│   └── auth.py                 # AuthService (không nằm packages/core)
└── alembic/versions/
    ├── 001_create_users.py
    └── 002_refresh_tokens_and_last_login.py

apps/api/src/api/
├── routes/auth.py              # 5 endpoints + rate limit
├── deps.py                     # get_current_user → raises AuthError
├── errors.py                   # AuthError global handler
├── rate_limit.py               # slowapi wrapper
└── main.py                     # CORS restricted, limiter state
```

> **Khác plan gốc:** `AuthService` nằm ở `packages/db/services/auth.py` (không phải `packages/core/auth/service.py`).

---

## 2. Security hardening đã áp dụng

### Critical

| ID | Vấn đề | Giải pháp đã code |
|----|--------|-------------------|
| C1 | Refresh `jti` không lưu DB | Bảng `refresh_tokens` + store/revoke on refresh |
| C2 | Race register → 500 | `IntegrityError` → `EmailExistsError` (409) |
| C3 | Logout chỉ xóa cookie | `logout()` revoke `jti` server-side; access TTL **15 phút** |
| C4 | Không rate limit | slowapi: login 5/min, register 10/min, refresh 3/min |

### Medium

| ID | Giải pháp |
|----|-----------|
| M1 | `PydanticCustomError` thay string parsing trong validation |
| M2 | Login inactive → `401 invalid_credentials` (không lộ account) |
| M3 | `TokenTypeMismatchError` code = `token_type_mismatch` |
| M4 | PG trigger `update_users_updated_at` (migration 002) |
| M5 | `display_name=""` → normalize `None` |
| M6 | `app_env: Literal["development","staging","production"]` |
| M7 | CORS: methods `GET/POST/OPTIONS`, headers restricted |

### Low

| ID | Giải pháp |
|----|-----------|
| L1 | `get_user_by_id(user_id: UUID)` typed |
| L2 | `create_refresh_token()` → `tuple[str, str]` |
| L3 | `deps.py` raise `AuthError` (unified với routes) |
| L5 | RS256 support (PEM keys) |
| L6 | `User.last_login_at` updated on login |

---

## 3. JWT & cookies (as-built)

| Setting | Giá trị |
|---------|---------|
| Access TTL | **15 phút** (was 60) |
| Refresh TTL | 7 ngày |
| Algorithm | HS256 (default) hoặc RS256 |
| Refresh rotation | Revoke old `jti` + issue new on each refresh |
| Logout | Revoke refresh `jti` + clear cookies |

---

## 4. Tests

**27 tests pass** (`apps/api/tests/`):

| File | Coverage |
|------|----------|
| `test_auth_api.py` | register/login/me, refresh rotation, logout revoke, inactive login, validation |
| `test_jwt.py` | HS256 + RS256 roundtrip, expiry, type mismatch |
| `test_password.py` | bcrypt roundtrip |
| `test_password_validation.py` | strength rules |
| `test_rate_limit.py` | login 429 after 5 attempts |

---

## 5. Config env (bổ sung so với plan gốc)

```env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
RATE_LIMIT_ENABLED=true
AUTH_LOGIN_RATE_LIMIT=5/minute
AUTH_REGISTER_RATE_LIMIT=10/minute
AUTH_REFRESH_RATE_LIMIT=3/minute
COOKIE_SECURE=              # optional override
JWT_ALGORITHM=HS256         # or RS256
JWT_PRIVATE_KEY=            # RS256 only
JWT_PUBLIC_KEY=             # RS256 only
```

---

## 6. Chưa implement

- Frontend Auth (Studio) — xem [03-frontend.md](./03-frontend.md)
- Email verification — xem [06-email-verification.md](./06-email-verification.md)
- Task ownership enforcement
- Redis access token blacklist (không cần với TTL 15 phút + refresh revocation)

---

## 7. Deploy checklist

1. `alembic upgrade head` (migration 002)
2. Cập nhật `.env` theo `.env.example`
3. Đổi `JWT_SECRET_KEY` khỏi default
4. Production: `APP_ENV=production` → `cookie_secure=true` tự động
