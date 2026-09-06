from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ApprovalAction
from app.models.base import CreatedAtMixin, ExpenseBase
from app.models.user import User

if TYPE_CHECKING:
    from app.models.expense import Expense


class ApprovalLog(ExpenseBase, CreatedAtMixin):
    __tablename__ = "approval_logs"

    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, native_enum=False, length=50),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    expense: Mapped[Expense] = relationship(
        "Expense",
        back_populates="approval_logs",
        lazy="selectin",
    )
    actor: Mapped[User] = relationship(
        User,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ApprovalLog id={self.id} expense_id={self.expense_id} action={self.action} actor_id={self.actor_id}>"
