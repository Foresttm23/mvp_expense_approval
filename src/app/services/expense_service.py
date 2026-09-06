from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ExpenseStatus
from app.core.exceptions.app import (
    InvalidStateTransitionError,
    NotFoundError,
    UnauthorizedActionError,
    ValidationError,
)
from app.models.expense import Expense
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.user_repo import UserRepository
from app.schemas.expense import ExpenseCreate


class ExpenseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._expense_repo = ExpenseRepository(session)
        self._user_repo = UserRepository(session)

    async def create_expense(
        self,
        applicant_id: uuid.UUID,
        payload: ExpenseCreate,
    ) -> Expense:
        """
        Create and route a new pending expense claim.

        Raises:
            ValidationError: If no approver is configured for the chosen category.
        """
        log = logger.bind(
            applicant_id=str(applicant_id),
            category=payload.category,
            amount=payload.amount,
        )

        approver = await self._user_repo.get_approver_by_category(payload.category)
        if approver is None:
            log.error("No approver configured for category")
            raise ValidationError(
                f"No approver is configured for category '{payload.category}'."
            )

        expense = await self._expense_repo.create(
            **payload.model_dump(),
            applicant_id=applicant_id,
            assigned_approver_id=approver.id,
            status=ExpenseStatus.PENDING,
        )
        await self._session.commit()

        log.bind(
            expense_id=str(expense.id),
            approver_id=str(approver.id),
        ).info("Expense claim created and routed")
        return expense

    async def withdraw_expense(
        self,
        expense_id: uuid.UUID,
        applicant_id: uuid.UUID,
    ) -> Expense:
        """
        Withdraw a pending claim owned by *applicant_id*.

        Raises:
            NotFoundError: If the expense does not exist.
            UnauthorizedActionError: If the caller is not the applicant.
            InvalidStateTransitionError: If the expense is not in ``pending`` state (already resolved).
        """
        log = logger.bind(
            expense_id=str(expense_id),
            applicant_id=str(applicant_id),
        )

        expense = await self._expense_repo.get_by_id_for_update(expense_id)
        if expense is None:
            raise NotFoundError(f"Expense '{expense_id}' not found.")

        if expense.applicant_id != applicant_id:
            log.warning("Withdrawal attempted by non-owner")
            raise UnauthorizedActionError(
                "Only the original applicant can withdraw this claim."
            )

        if expense.status != ExpenseStatus.PENDING:
            log.warning(
                "Withdrawal rejected — expense already resolved",
                current_status=expense.status,
            )
            raise InvalidStateTransitionError(
                f"Cannot withdraw an expense that is already '{expense.status}'. "
                "Only pending claims may be withdrawn."
            )

        expense = await self._expense_repo.update(
            expense, status=ExpenseStatus.WITHDRAWN
        )
        await self._session.commit()

        log.info("Expense claim withdrawn")
        return expense

    async def get_applicant_expenses(
        self,
        applicant_id: uuid.UUID,
        *,
        status: ExpenseStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """
        Retrieve paginated expense claims submitted by an applicant.

        Optionally filters by approval/review status for display in user dashboards.

        Returns:
            ``(items, total_count)`` pair.
        """
        return await self._expense_repo.get_by_applicant(
            applicant_id,
            status=status,
            offset=offset,
            limit=limit,
        )

    async def get_expense_for_applicant(
        self,
        expense_id: uuid.UUID,
        applicant_id: uuid.UUID,
    ) -> Expense:
        """
        Return a specific claim visible to the applicant.

        Raises:
            NotFoundError: If the expense does not exist or is not accessible by *applicant_id*.
        """
        expense = await self._expense_repo.get_by_id_scoped(expense_id, applicant_id)
        if expense is None:
            raise NotFoundError(
                f"Expense '{expense_id}' not found or you do not have access to it."
            )
        return expense
