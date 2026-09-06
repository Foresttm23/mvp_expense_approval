from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ExpenseStatus
from app.models.expense import Expense
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    model = Expense

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_applicant(
        self,
        applicant_id: uuid.UUID,
        *,
        status: ExpenseStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """
        Query expenses by applicant ID ordered by creation date descending.

        Returns
        -------
        ``(items, total_count)`` pair of claims submitted by *applicant_id*.
        """
        stmt = (
            select(Expense)
            .where(Expense.applicant_id == applicant_id)
            .order_by(Expense.created_at.desc())
        )
        if status is not None:
            stmt = stmt.where(Expense.status == status)

        items = await self.paginate_query(stmt, offset=offset, limit=limit)
        total = await self.count(stmt)
        return items, total

    async def get_approver_queue(
        self,
        approver_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Expense], int]:
        """
        Returns
        -------
        *pending* claims assigned to the given approver.
        FIFO order.
        """
        stmt = (
            select(Expense)
            .where(
                Expense.assigned_approver_id == approver_id,
                Expense.status == ExpenseStatus.PENDING,
            )
            .order_by(Expense.created_at.asc())
        )
        items = await self.paginate_query(stmt, offset=offset, limit=limit)
        total = await self.count(stmt)
        return items, total

    async def get_by_id_scoped(
        self,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Expense | None:
        """
        Retrieve an expense if *user_id* == *applicant_id* or *user_id* == *assigned_approver_id*.

        Returns ``None`` when the expense does not exist or the caller has no access to it.
        """
        stmt = select(Expense).where(
            Expense.id == expense_id,
            (Expense.applicant_id == user_id) | (Expense.assigned_approver_id == user_id),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(
        self,
        expense_id: uuid.UUID,
    ) -> Expense | None:
        """
        Retrieve an expense by ID with an exclusive row lock (FOR UPDATE).

        Guarantees final state.
        """
        stmt = (
            select(Expense)
            .where(Expense.id == expense_id)
            .with_for_update()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

