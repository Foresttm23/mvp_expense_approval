from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ApprovalAction
from app.models.approval import ApprovalLog
from app.repositories.base import BaseRepository


class ApprovalRepository(BaseRepository[ApprovalLog]):
    model = ApprovalLog

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def create_log(
        self,
        *,
        expense_id: uuid.UUID,
        actor_id: uuid.UUID,
        action: ApprovalAction,
        comment: str | None = None,
    ) -> ApprovalLog:
        return await self.create(
            expense_id=expense_id,
            actor_id=actor_id,
            action=action,
            comment=comment,
        )

    async def get_logs_for_expense(
        self,
        expense_id: uuid.UUID,
    ) -> list[ApprovalLog]:
        stmt = (
            select(ApprovalLog)
            .where(ApprovalLog.expense_id == expense_id)
            .order_by(ApprovalLog.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
