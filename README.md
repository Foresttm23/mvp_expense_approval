# MVP Expense Approval System

A production-ready, async RESTful API coordinating organizational financial reimbursement claims with automated category routing, strict state transitions, and an AI-assisted review advisory.

---

## Tech Stack

- **Language & Runtime**: Python 3.13+ (strict typing, PEP 695 generics)
- **Web Framework**: FastAPI (with `Annotated` dependency injection)
- **Database & ORM**: PostgreSQL via `asyncpg` & SQLAlchemy 2.0 (async sessions)
- **Migrations**: Alembic
- **Authentication & Security**: PyJWT (`HS256`), `pwdlib` (`Argon2`), OAuth2 Password Bearer flow
- **Validation**: Pydantic v2
- **Logging**: Loguru (structured logging with contextual bindings)

---

## Architectural Highlights

The service follows a lightweight layered architecture:
```text
src/app/
├── api/             # Presentation layer: dependencies, route handlers & response formatting
├── models/          # SQLAlchemy 2.0 ORM Declarative Models
├── repositories/    # Data access layer: async queries, pagination & scoped retrieval
├── schemas/         # Pydantic v2 DTOs (Request / Response models)
└── services/        # Business logic: state transitions, routing, AI advisory & auth
```

---

## Authentication & Token Policy Notes

### Future Token Revocation (`iat` & `token_revoked_before`)

> [!NOTE]
> **Token Revocation Architecture (Future Feature)**
> 
> - **JWT `iat` Claim**: Every access token issued via `core/security.py` includes an **Issued At (`iat`)** timestamp claim representing UTC Unix epoch seconds.
> - **`User.token_revoked_before` Field**: The `User` ORM model contains a nullable timezone-aware datetime column `token_revoked_before: Mapped[datetime | None]`.
> - **Design Intent**: For the MVP, token invalidation relies on short-lived tokens (60-minute TTL) and immediate account deactivation via `is_active = False`. The `token_revoked_before` column and `iat` claim are pre-configured to enable instantaneous single-user or global session revocation in a future release:
>   ```python
>   # Planned verification in auth validation pipeline:
>   if user.token_revoked_before is not None:
>       token_iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
>       if token_iat < user.token_revoked_before:
>           raise UnauthorizedActionError("Token has been revoked.")
>   ```
> - Calling a future `/auth/logout` or `/auth/revoke-all` endpoint will set `user.token_revoked_before = datetime.now(UTC)` to instantly invalidate all previously issued tokens for that account.

---

## Local Development

### 1. Environment Setup

Copy `.env.sample` to `.env` and configure variables:
```bash
cp .env.sample .env
```

### 2. Install Dependencies

Using [uv](https://github.com/astral-sh/uv):
```bash
uv sync
```

### 3. Run Migrations

```bash
uv run alembic upgrade head
```

### 4. Run Development Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
