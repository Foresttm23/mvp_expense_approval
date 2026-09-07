from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.enums import AIAnalysisStatus, ExpenseCategory, ExpenseStatus
from tests.helpers import (
    auth_headers,
    login_and_get_token,
    make_expense_payload,
    register_and_verify_token,
    submit_expense,
)

pytestmark = pytest.mark.asyncio

_OFFICE_APPROVER_EMAIL = "approver_office@example.com"
_OFFICE_APPROVER_PASSWORD = "password123"

_TRAVEL_APPROVER_EMAIL = "approver_travel@example.com"
_TRAVEL_APPROVER_PASSWORD = "password123"


class TestEmployeeIsolation:
    async def test_employee_cannot_read_another_employees_claim(
        self, client: AsyncClient
    ) -> None:
        token_a = await register_and_verify_token(client)
        expense = await submit_expense(client, token_a, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        token_b = await register_and_verify_token(client)
        resp = await client.get(
            f"/api/v1/expenses/{expense_id}", headers=auth_headers(token_b)
        )
        assert resp.status_code in {403, 404}


class TestApproverIsolation:
    async def test_wrong_approver_cannot_approve_claim(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        travel_token = await login_and_get_token(
            client, _TRAVEL_APPROVER_EMAIL, _TRAVEL_APPROVER_PASSWORD
        )
        resp = await client.post(
            f"/api/v1/approvals/{expense_id}/approve",
            headers=auth_headers(travel_token),
        )
        assert resp.status_code in {403, 404}

    async def test_wrong_approver_cannot_review_unassigned_claim(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)

        travel_token = await login_and_get_token(
            client, _TRAVEL_APPROVER_EMAIL, _TRAVEL_APPROVER_PASSWORD
        )
        resp = await client.get(
            f"/api/v1/approvals/{expense['id']}", headers=auth_headers(travel_token)
        )
        assert resp.status_code in {403, 404}


class TestRoleEnforcement:
    async def test_employee_only_blocked_from_approvals_queue(
        self, client: AsyncClient
    ) -> None:
        token = await register_and_verify_token(client)
        resp = await client.get(
            "/api/v1/approvals/queue", headers=auth_headers(token)
        )
        assert resp.status_code == 403

    async def test_approver_only_blocked_from_submitting_expense(
        self, client: AsyncClient
    ) -> None:
        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        resp = await client.post(
            "/api/v1/expenses",
            json=make_expense_payload(),
            headers=auth_headers(appr_token),
        )
        assert resp.status_code == 403

    async def test_unauthenticated_request_blocked(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/approvals/queue")
        assert resp.status_code == 401


class TestAIFallback:
    async def test_review_succeeds_even_when_ai_provider_fails(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )

        with patch(
            "app.services.providers.gemini_provider.GeminiProvider.analyse",
            new_callable=AsyncMock,
            side_effect=Exception("AI backend is down"),
        ):
            resp = await client.get(
                f"/api/v1/approvals/{expense_id}", headers=auth_headers(appr_token)
            )

        assert resp.status_code == 200
        ai = resp.json()["ai_analysis"]
        assert ai["status"] in {AIAnalysisStatus.ERROR, AIAnalysisStatus.UNAVAILABLE}
        assert ai["summary"] is None

    async def test_approve_succeeds_even_when_ai_is_down(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )

        with patch(
            "app.services.providers.gemini_provider.GeminiProvider.analyse",
            new_callable=AsyncMock,
            side_effect=RuntimeError("network error"),
        ):
            resp = await client.post(
                f"/api/v1/approvals/{expense_id}/approve",
                headers=auth_headers(appr_token),
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == ExpenseStatus.APPROVED
