# MVP Expense Approval System

A production-ready, async RESTful API coordinating organizational financial reimbursement claims with automated category routing, strict state transitions, and an AI-assisted review advisory.

---

## Overview & Core Workflow

The service coordinates internal financial reimbursement claims (*expense claims*) within an organization:

1. **Submission & Automatic Routing**: An employee submits an expense claim with an amount (USD), category, description, expense date, and payment details. The system automatically routes and assigns the designated approver based on the chosen category (`OFFICE`, `TRAVEL`, `CLIENT_ENTERTAINMENT`, `SOFTWARE_SUBSCRIPTIONS`, `OTHER`).
2. **Review & AI Advisory**: When an assigned approver opens a claim from their queue, an integrated AI advisory generates a 1–2 sentence executive summary and flags potential inconsistencies (e.g., category is `OFFICE` but description mentions flights). The AI advisory is strictly non-blocking: if the model times out or fails, review and approval proceed unaffected.
3. **Approval Decision**: The assigned approver approves or rejects the claim. Rejections strictly require a non-empty reason.
4. **Applicant Control**: The applicant can withdraw a claim at any point while it is still `pending`. Once resolved (`approved`, `rejected`, or `withdrawn`), the state is immutable.
5. **Dual-Role & Data Isolation**: Users can hold both `employee` and `approver` roles concurrently. Strict scoping guarantees employees only access their own submissions and approvers only access claims routed to them.

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

## Authentication Notes

- **JWT Tokens**: Standard 60-minute bearer tokens.
- **Session Revocation**: The `User` model includes a `token_revoked_before` timestamp column and an `iat` claim in the JWT. This makes it easy to add single-user session revocation (e.g. `/auth/logout`) in the future without database schema changes.

---

## AI Advisory

- **Provider-Agnostic**: Core business logic depends on an abstract `LLMProvider` interface rather than calling the Gemini SDK directly. Gemini is plugged in as an adapter in `services/providers/gemini_provider.py`.
- **On-Demand**: Triggered when an approver opens a claim for review (`GET /api/v1/approvals/{id}`).
- **Graceful Fallback**: Wrapped in a 3.0s timeout. If the LLM is slow, down, or missing an API key, it returns a fallback response so the approver's workflow is never blocked.

### Future Improvements

> If expanding this beyond an MVP, a few things could be improved:
>
> - **Faster page loads**: Right now, the AI analysis runs during the expense review request. We could split it into a separate endpoint so the expense details show up instantly while the AI summary loads in the background.
> - **Caching**: If an approver re-opens the same expense, we could cache the previous AI response so we don't pay for the same LLM call twice.

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

### 5. Running Tests

```bash
uv run pytest
```

### 6. Running with Docker Compose

To start both PostgreSQL and the API service in containers:
```bash
docker compose up --build
```

Interactive API documentation will be available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

