
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.enums import UserRole
from tests.helpers import (
    auth_headers,
    make_user_payload,
    register_and_verify_token,
    unique_email,
)

pytestmark = pytest.mark.asyncio


class TestRegistration:
    async def test_register_returns_token(self, client: AsyncClient) -> None:
        payload = make_user_payload(email=unique_email("emp"))
        resp = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_duplicate_email_conflict(self, client: AsyncClient) -> None:
        payload = make_user_payload(email=unique_email("dup"))
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409

    async def test_register_weak_password_rejected(self, client: AsyncClient) -> None:
        payload = make_user_payload(
            email=unique_email("weak"), password="short"
        )
        resp = await client.post(
            "/api/v1/auth/register",
            json=payload,
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_correct_credentials(self, client: AsyncClient) -> None:
        email = unique_email("login")
        password = "mypassword!"
        await register_and_verify_token(client, email=email, password=password)

        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password_returns_401(self, client: AsyncClient) -> None:
        email = unique_email("badpw")
        await register_and_verify_token(client, email=email, password="correctpass")

        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "wrongpass"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_user_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@nowhere.com", "password": "anything"},
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_returns_current_user(self, client: AsyncClient) -> None:
        email = unique_email("me")
        token = await register_and_verify_token(client, email=email)

        resp = await client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == email
        assert UserRole.EMPLOYEE in body["roles"]

    async def test_me_without_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401
