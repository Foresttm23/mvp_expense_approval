from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.enums import ExpenseCategory, ExpenseStatus
from tests.helpers import (
    auth_headers,
    login_and_get_token,
    register_and_verify_token,
    submit_expense,
)

pytestmark = pytest.mark.asyncio

_OFFICE_APPROVER_EMAIL = "approver_office@example.com"
_OFFICE_APPROVER_PASSWORD = "password123"

_TRAVEL_APPROVER_EMAIL = "approver_travel@example.com"
_TRAVEL_APPROVER_PASSWORD = "password123"


class TestApproveWorkflow:
    async def test_submit_and_approve_full_cycle(self, client: AsyncClient) -> None:
        # 1. Register employee
        emp_token = await register_and_verify_token(client)

        # 2. Submit an OFFICE expense
        expense = await submit_expense(
            client, emp_token, category=ExpenseCategory.OFFICE, amount="250.00"
        )
        expense_id = expense["id"]

        assert expense["status"] == ExpenseStatus.PENDING
        assert expense["assigned_approver_id"] is not None

        # 3. Approver logs in
        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )

        # 4. Queue endpoint responds
        queue_resp = await client.get(
            "/api/v1/approvals/queue", headers=auth_headers(appr_token)
        )
        assert queue_resp.status_code == 200

        # 5. Approver can review this specific claim
        review_resp = await client.get(
            f"/api/v1/approvals/{expense_id}", headers=auth_headers(appr_token)
        )
        assert review_resp.status_code == 200
        review_body = review_resp.json()
        assert review_body["expense"]["id"] == expense_id
        assert "ai_analysis" in review_body

        # 6. Approver approves
        approve_resp = await client.post(
            f"/api/v1/approvals/{expense_id}/approve",
            headers=auth_headers(appr_token),
        )
        assert approve_resp.status_code == 200
        approved = approve_resp.json()
        assert approved["status"] == ExpenseStatus.APPROVED

        # 7. Employee sees the updated status
        detail_resp = await client.get(
            f"/api/v1/expenses/{expense_id}", headers=auth_headers(emp_token)
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["status"] == ExpenseStatus.APPROVED

    async def test_double_approve_is_rejected(self, client: AsyncClient) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )

        r1 = await client.post(
            f"/api/v1/approvals/{expense_id}/approve",
            headers=auth_headers(appr_token),
        )
        assert r1.status_code == 200

        r2 = await client.post(
            f"/api/v1/approvals/{expense_id}/approve",
            headers=auth_headers(appr_token),
        )
        assert r2.status_code == 422


class TestRejectWorkflow:
    async def test_submit_and_reject_with_reason(self, client: AsyncClient) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        reject_resp = await client.post(
            f"/api/v1/approvals/{expense_id}/reject",
            json={"reason": "Amount exceeds the category limit."},
            headers=auth_headers(appr_token),
        )
        assert reject_resp.status_code == 200
        body = reject_resp.json()
        assert body["status"] == ExpenseStatus.REJECTED
        assert body["rejection_reason"] == "Amount exceeds the category limit."

    async def test_reject_without_reason_is_unprocessable(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        resp = await client.post(
            f"/api/v1/approvals/{expense_id}/reject",
            json={},
            headers=auth_headers(appr_token),
        )
        assert resp.status_code == 422

    async def test_reject_with_empty_reason_is_unprocessable(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        resp = await client.post(
            f"/api/v1/approvals/{expense_id}/reject",
            json={"reason": "   "},
            headers=auth_headers(appr_token),
        )
        assert resp.status_code == 422


class TestWithdrawWorkflow:
    async def test_employee_can_withdraw_pending_claim(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.TRAVEL)
        expense_id = expense["id"]

        resp = await client.post(
            f"/api/v1/expenses/{expense_id}/withdraw",
            headers=auth_headers(emp_token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == ExpenseStatus.WITHDRAWN

    async def test_withdraw_already_approved_claim_fails(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(client, emp_token, category=ExpenseCategory.OFFICE)
        expense_id = expense["id"]

        # Approve first
        appr_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        await client.post(
            f"/api/v1/approvals/{expense_id}/approve",
            headers=auth_headers(appr_token),
        )

        # Then try to withdraw
        resp = await client.post(
            f"/api/v1/expenses/{expense_id}/withdraw",
            headers=auth_headers(emp_token),
        )
        assert resp.status_code == 422


class TestCategoryRouting:
    async def test_travel_claim_routed_to_travel_approver(
        self, client: AsyncClient
    ) -> None:
        emp_token = await register_and_verify_token(client)
        expense = await submit_expense(
            client,
            emp_token,
            category=ExpenseCategory.TRAVEL,
            description="Flight to client site",
            amount="800.00",
        )
        expense_id = expense["id"]

        # Travel approver can review this claim
        travel_token = await login_and_get_token(
            client, _TRAVEL_APPROVER_EMAIL, _TRAVEL_APPROVER_PASSWORD
        )
        travel_resp = await client.get(
            f"/api/v1/approvals/{expense_id}", headers=auth_headers(travel_token)
        )
        assert travel_resp.status_code == 200

        # OFFICE approver is denied access
        office_token = await login_and_get_token(
            client, _OFFICE_APPROVER_EMAIL, _OFFICE_APPROVER_PASSWORD
        )
        office_resp = await client.get(
            f"/api/v1/approvals/{expense_id}", headers=auth_headers(office_token)
        )
        assert office_resp.status_code in {403, 404}
