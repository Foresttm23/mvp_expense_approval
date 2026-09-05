from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import ExpenseCategory
from app.models.expense import CategoryApprover
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_approver_by_category(
        self, category: ExpenseCategory
    ) -> User | None:
        """Find the approver for a category (DB, then fallback to config)."""
        stmt = (
            select(User)
            .join(CategoryApprover, CategoryApprover.approver_id == User.id)
            .where(CategoryApprover.category == category)
        )
        result = await self._session.execute(stmt)
        approver = result.scalar_one_or_none()
        if approver:
            return approver

        return await self._fallback_category_approver(category)


    async def _fallback_category_approver(self, category: ExpenseCategory) -> User | None:
        """Find the approver for a category from the fallback map."""
        fallback_email = get_settings().DEFAULT_CATEGORY_APPROVERS.get(
            category.value
        )
        if fallback_email:
            return await self.get_by_email(fallback_email)

        return None

