from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def list_paginated(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[ModelType], int]:
        safe_limit = min(max(limit, 1), 100)
        safe_offset = max(offset, 0)

        stmt = (
            select(self.model)
            .order_by(self.model.created_at.desc())
            .offset(safe_offset)
            .limit(safe_limit)
        )

        items_res = await self._session.execute(stmt)
        total = await self.count()

        return list(items_res.scalars().all()), total

    async def count(self) -> int:
        """Return the total number of records for the model."""
        result = await self._session.execute(
            select(func.count()).select_from(self.model)
        )
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
