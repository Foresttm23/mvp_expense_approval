"""Shared helper functions for HTTP integration tests."""
from __future__ import annotations

import uuid
from typing import Any

from httpx import AsyncClient

from app.core.enums import ExpenseCategory
from app.schemas.user import UserCreate


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}+{uuid.uuid4().hex[:8]}@test.example"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_user_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "email": unique_email(),
        "password": "password123",
        "full_name": "Test User",
    }
    base.update(overrides)
    return base


async def register_and_verify_token(
    client: AsyncClient,
    payload: dict[str, Any] | UserCreate | None = None,
    **overrides: Any,
) -> str:
    if payload is None:
        payload = make_user_payload(**overrides)

    json_body = (
        payload.model_dump()
        if isinstance(payload, UserCreate)
        else payload
    )

    resp = await client.post(
        "/api/v1/auth/register",
        json=json_body,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


async def login_and_get_token(
    client: AsyncClient,
    email: str,
    password: str = "password123",
) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def make_expense_payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "amount": "150.00",
        "category": ExpenseCategory.OFFICE,
        "description": "Ergonomic desk chair for home office",
        "expense_date": "2025-06-15",
        "payment_details": "IBAN: DE89370400440532013000",
    }
    base.update(overrides)
    if isinstance(base.get("category"), ExpenseCategory):
        base["category"] = base["category"].value
    return base


async def submit_expense(
    client: AsyncClient,
    token: str,
    **overrides: Any,
) -> dict[str, Any]:
    resp = await client.post(
        "/api/v1/expenses",
        json=make_expense_payload(**overrides),
        headers=auth_headers(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
