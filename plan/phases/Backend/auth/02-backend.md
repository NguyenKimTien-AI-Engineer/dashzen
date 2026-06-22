# 02 — Backend Implementation (FastAPI)

> Auth subsystem nằm ở **`apps/api`** + **`packages/core`** + **`packages/db`** — không thuộc Agent Runtime 11 subsystem.
>
> **Nguyên tắc:** `apps/api` là adapter mỏng; logic auth trong `packages/core/auth/` + `packages/db/services/auth.py`.

**Trạng thái:** Backend Auth **đã implement** — xem [07-implementation-status.md](./07-implementation-status.md).

---

## 1. Cấu trúc file (as-built)

```
packages/
├── core/src/core/
│   ├── auth/
│   │   ├── jwt.py              # encode, decode; HS256 + RS256
│   │   ├── password.py         # bcrypt hash/verify
│   │   ├── cookies.py          # set/clear response cookies
│   │   └── validation.py       # password strength rules
│   ├── config.py               # JWT_*, rate limit, AppEnv enum
│   ├── exceptions.py             # AuthError hierarchy
│   └── schemas/
│       ├── auth.py             # LoginRequest, UserResponse, RegisterRequest
│       └── validation.py       # format_validation_errors
│
└── db/src/db/
    ├── models/
    │   ├── user.py             # User (+ last_login_at)
    │   └── refresh_token.py    # jti, revoked, expires_at
    ├── repositories/
    │   ├── user.py
    │   └── refresh_token.py
    ├── services/
    │   └── auth.py             # AuthService
    └── alembic/versions/
        ├── 001_create_users.py
        └── 002_refresh_tokens_and_last_login.py

apps/api/src/api/
├── routes/
│   └── auth.py                 # POST login, register, refresh, logout, GET me
├── deps.py                     # get_current_user (raises AuthError)
├── errors.py                   # AuthError → JSONResponse
├── rate_limit.py               # slowapi wrapper
└── main.py                     # CORS + limiter
```

---

## 1.1 Prerequisite — Docker PostgreSQL

Trước khi implement Auth backend, chạy Postgres theo [00-docker-postgres.md](./00-docker-postgres.md):

```bash
docker compose -f infra/compose/docker-compose.yml up -d
```

`DATABASE_URL=postgresql+asyncpg://dashzen:dashzen@localhost:5432/dashzen`

---

## 2. Database — User model

```python
# packages/db/src/db/models/user.py

class User(Base):
    __tablename__ = "users"

    id: UUID
    email: str                  # unique, indexed, lowercase at persistence
    password_hash: str          # bcrypt — NEVER store plain password
    display_name: str | None
    is_active: bool = True
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime        # PG trigger on UPDATE (migration 002)
```

### Refresh tokens

```python
# packages/db/src/db/models/refresh_token.py

class RefreshToken(Base):
    jti: str                    # PK
    user_id: UUID               # FK users.id CASCADE
    expires_at: datetime
    revoked: bool = False
    created_at: datetime
```

**Migrations:**

```bash
uv run alembic -c packages/db/alembic.ini upgrade head
```

---

## 3. Password hashing

| Concern | Implementation |
|---------|----------------|
| Library | `bcrypt` |
| Cost factor | 12 |
| Register | hash trước khi insert |
| Login | `verify_password(plain, hash)` → bool |
| Validation | min 8 chars, 1 letter, 1 digit (`PydanticCustomError`) |

---

## 4. JWT service

```python
# packages/core/src/core/auth/jwt.py

def create_access_token(user_id: UUID, email: str) -> str: ...
def create_refresh_token(user_id: UUID) -> tuple[str, str]: ...  # (token, jti)
def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> TokenPayload: ...
```

**Algorithms:** HS256 (default) hoặc RS256 (PEM keys).

**Exceptions (map → HTTP via `errors.py`):**

| Exception | HTTP | code |
|-----------|------|------|
| `TokenExpiredError` | 401 | `token_expired` |
| `TokenInvalidError` | 401 | `token_invalid` |
| `TokenTypeMismatchError` | 401 | `token_type_mismatch` |

---

## 5. Auth service

```python
# packages/db/src/db/services/auth.py

class AuthService:
    async def register(email, password, display_name?) -> User: ...
    async def login(email, password) -> User: ...
    async def refresh(refresh_token: str) -> tuple[User, TokenPair]: ...
    async def logout(refresh_token: str | None) -> None: ...
    async def issue_tokens(user: User) -> TokenPair: ...
```

**Business rules (as-built):**

- Email unique — register duplicate → 409 (`EmailExistsError`)
- Race condition register — `IntegrityError` → 409
- Password min 8 + letter + digit — Pydantic validation
- `is_active=False` → login **401** `invalid_credentials` (không lộ account)
- `get_current_user` + inactive → **403** `user_inactive`
- Refresh: validate `jti` in DB, not revoked, not expired → rotate
- Logout: revoke `jti` + clear cookies
- Login: update `last_login_at`

---

## 6. API routes

| Method | Path | Handler | Cookie | Rate limit |
|--------|------|---------|--------|------------|
| `POST` | `/v1/auth/register` | create user + auto-login | set both | 10/min |
| `POST` | `/v1/auth/login` | validate + issue tokens | set both | 5/min |
| `POST` | `/v1/auth/refresh` | validate refresh + rotate | set both | 3/min |
| `POST` | `/v1/auth/logout` | revoke jti + clear session | clear both | — |
| `GET` | `/v1/auth/me` | current user profile | — | — |

> **Planned:** Register sẽ đổi khi có email verification — xem [06-email-verification.md](./06-email-verification.md).

---

## 7. FastAPI dependencies

```python
# apps/api/src/api/deps.py

async def get_current_user(request, session) -> User:
    """
    1. Read access token: Cookie OR Authorization Bearer
    2. decode_token(type=access)
    3. Load user from DB by sub
    4. Verify is_active → UserInactiveError (403)
    5. Return User or raise AuthError (401)
    """
```

**Error handling:** `deps.py` raise `AuthError` subclasses — `errors.py` map sang JSON.

---

## 8. CORS & credentials

```python
# apps/api/src/api/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Cookie"],
)
```

---

## 9. Config (env)

```env
APP_ENV=development
JWT_SECRET_KEY=change-me-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
RATE_LIMIT_ENABLED=true
AUTH_LOGIN_RATE_LIMIT=5/minute
AUTH_REGISTER_RATE_LIMIT=10/minute
AUTH_REFRESH_RATE_LIMIT=3/minute
API_CORS_ORIGINS=http://localhost:3000
```

---

## 10. Error responses (auth-specific)

| Status | Code | Khi nào |
|--------|------|---------|
| 400 | `validation_error` | Form invalid |
| 401 | `invalid_credentials` | Login sai / inactive |
| 401 | `token_expired` | Access/refresh hết hạn |
| 401 | `token_invalid` | Signature sai / malformed / revoked jti |
| 401 | `token_type_mismatch` | Dùng refresh token làm access |
| 403 | `user_inactive` | Account disabled (authenticated `/me`) |
| 409 | `email_exists` | Register trùng email |
| 429 | — | Rate limit exceeded (slowapi) |

```json
{
  "error": {
    "code": "invalid_credentials",
    "message": "Invalid email or password."
  }
}
```

---

## 11. Task ownership

Mọi query Task phải filter `user_id` — **chưa implement** (Slice 1b).

---

## 12. Testing (backend) — Done

| Test | Status |
|------|--------|
| `hash_password` / `verify_password` roundtrip | ✓ |
| `create_access_token` → `decode_token` | ✓ |
| RS256 roundtrip | ✓ |
| `POST /login` → cookie → `GET /me` | ✓ |
| Refresh rotation + revoke old token | ✓ |
| Logout revokes refresh | ✓ |
| Rate limit 429 | ✓ |
| Inactive login → 401 generic | ✓ |

**27 tests pass** — `pytest apps/api/tests`

---

## 13. Dependencies (pyproject)

`packages/core`:
```toml
"pyjwt[crypto]>=2.9",
"bcrypt>=4.2",
```

`apps/api`:
```toml
"slowapi>=0.1.9",
```

---

## 14. Thứ tự code

- [x] Docker Postgres
- [x] `.env` — `DATABASE_URL` + `JWT_SECRET_KEY`
- [x] `User` model + migration 001
- [x] `password.py`, `jwt.py`
- [x] `AuthService` + refresh token revocation
- [x] `routes/auth.py` + rate limit
- [x] `deps.get_current_user`
- [x] CORS middleware (restricted)
- [x] Migration 002 (refresh_tokens, last_login_at, trigger)
- [x] pytest auth suite (27 tests)
- [ ] Email verification — [06-email-verification.md](./06-email-verification.md)
- [ ] Protect `/v1/tasks/*`
