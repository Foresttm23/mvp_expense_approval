from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from app.models.base import ExpenseBase


class BaseRepository[ModelType: ExpenseBase]:
    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **kwargs: Any) -> ModelType:
        instance = self.model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def get_by_id(self, pk: UUID) -> ModelType | None:
        result = await self._session.execute(
            select(self.model).where(self.model.id == pk)
        )
        return result.scalar_one_or_none()

    async def paginate_query(
        self,
        stmt: Select[tuple[ModelType]],
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ModelType]:
        safe_limit = min(max(limit, 1), 100)
        safe_offset = max(offset, 0)
        paged_stmt = stmt.offset(safe_offset).limit(safe_limit)
        res = await self._session.execute(paged_stmt)
        return list(res.scalars().all())

    async def count(self, stmt: Select | None = None) -> int:
        if stmt is not None:
            # Strip order_by as it not needed for count
            count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        else:
            count_stmt = select(func.count()).select_from(self.model)
        result = await self._session.execute(count_stmt)
        return result.scalar_one()

    async def update(self, instance: ModelType, **kwargs: Any) -> ModelType:
        """Apply *kwargs* and flush."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        self._session.add(instance)
        await self._session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self._session.delete(instance)
        await self._session.flush()
