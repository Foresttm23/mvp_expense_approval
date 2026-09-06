from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalAction, ExpenseStatus
from app.core.exceptions.app import (
    InvalidStateTransitionError,
    NotFoundError,
    UnauthorizedActionError,
)
from app.models.expense import Expense
from app.repositories.approval_repo import ApprovalRepository
from app.repositories.expense_repo import ExpenseRepository

if TYPE_CHECKING:
    from loguru import Logger


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._expense_repo = ExpenseRepository(session)
        self._approval_repo = ApprovalRepository(session)

    async def get_queue(
        self,
        approver_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """
        Return *pending* claims assigned to the given approver (FIFO).

        Returns
        -------
        ``(items, total_count)`` pair.
        """
        return await self._expense_repo.get_approver_queue(
            approver_id,
            offset=offset,
            limit=limit,
        )

    async def get_expense_for_approver(
        self,
        expense_id: uuid.UUID,
        approver_id: uuid.UUID,
    ) -> Expense:
        """
        Return a specific expense visible to the approver.

        Raises
        ------
        NotFoundError
            If the expense does not exist or is not assigned to *approver_id*.
        """
        expense = await self._expense_repo.get_by_id_scoped(expense_id, approver_id)
        if expense is None:
            raise NotFoundError(
                f"Expense '{expense_id}' not found or you do not have access to it."
            )
        return expense

    async def approve_expense(
        self,
        expense_id: uuid.UUID,
        approver_id: uuid.UUID,
    ) -> Expense:
        """
        Approve a pending claim assigned to *approver_id*.

        Returns
        -------
        Expense
            The updated expense in ``approved`` state.

        Raises
        ------
        NotFoundError
            If the expense does not exist.
        UnauthorizedActionError
            If *approver_id* is not the assigned approver.
        InvalidStateTransitionError
            If the expense is not in ``pending`` state.
        """
        log = logger.bind(
            expense_id=str(expense_id),
            approver_id=str(approver_id),
        )

        expense = await self._get_and_verify_expense(expense_id, approver_id, log)
        expense = await self._expense_repo.update(
            expense, status=ExpenseStatus.APPROVED
        )
        await self._approval_repo.create_log(
            expense_id=expense_id,
            actor_id=approver_id,
            action=ApprovalAction.APPROVE,
        )
        await self._session.commit()

        log.info("Expense claim approved")
        return expense

    async def reject_expense(
        self,
        expense_id: uuid.UUID,
        approver_id: uuid.UUID,
        reason: str,
    ) -> Expense:
        """
        Reject a pending claim with a mandatory non-empty reason.

        Returns
        -------
        Expense
            The updated expense in ``rejected`` state.

        Raises
        ------
        NotFoundError
            If the expense does not exist.
        UnauthorizedActionError
            If *approver_id* is not the assigned approver.
        InvalidStateTransitionError
            If the expense is not in ``pending`` state.
        ValueError
            If *reason* is empty or contains only whitespace.
        """
        stripped_reason = reason.strip()
        if not stripped_reason:
            raise ValueError("Rejection reason cannot be empty or whitespace only.")

        log = logger.bind(
            expense_id=str(expense_id),
            approver_id=str(approver_id),
        )

        expense = await self._get_and_verify_expense(expense_id, approver_id, log)
        expense = await self._expense_repo.update(
            expense,
            status=ExpenseStatus.REJECTED,
            rejection_reason=stripped_reason,
        )

        await self._approval_repo.create_log(
            expense_id=expense_id,
            actor_id=approver_id,
            action=ApprovalAction.REJECT,
            comment=stripped_reason,
        )
        await self._session.commit()

        log.info("Expense claim rejected")
        return expense

    async def _get_and_verify_expense(
        self, expense_id: uuid.UUID, approver_id: uuid.UUID, log: Logger
    ) -> Expense:
        expense = await self._expense_repo.get_by_id_for_update(expense_id)
        if expense is None:
            raise NotFoundError(f"Expense '{expense_id}' not found.")

        self._assert_is_assigned_approver(expense, approver_id, log)
        self._assert_is_pending(expense, log)
        return expense

    @staticmethod
    def _assert_is_assigned_approver(
        expense: Expense,
        approver_id: uuid.UUID,
        log: Logger,
    ) -> None:
        if expense.assigned_approver_id != approver_id:
            log.warning("Action attempted by non-assigned approver")
            raise UnauthorizedActionError(
                "You are not the assigned approver for this expense."
            )

    @staticmethod
    def _assert_is_pending(
        expense: Expense,
        log: Logger,
    ) -> None:
        if expense.status != ExpenseStatus.PENDING:
            log.warning(
                "Decision attempted on non-pending expense",
                current_status=expense.status,
            )
            raise InvalidStateTransitionError(
                f"Cannot process an expense that is already '{expense.status}'. "
                "Only pending claims may be approved or rejected."
            )
