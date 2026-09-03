from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ExpenseCategory, ExpenseStatus
from app.models.base import CreatedAtMixin, ExpenseBase, UpdatedAtMixin

if TYPE_CHECKING:
    from app.models.approval import ApprovalLog
    from app.models.user import User


class Expense(ExpenseBase, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    applicant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    payment_details: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, native_enum=False, length=20),
        default=ExpenseStatus.PENDING,
        nullable=False,
        index=True,
    )
    assigned_approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    applicant: Mapped[User] = relationship(
        "User",
        foreign_keys=[applicant_id],
        lazy="selectin",
    )
    assigned_approver: Mapped[User] = relationship(
        "User",
        foreign_keys=[assigned_approver_id],
        lazy="selectin",
    )
    approval_logs: Mapped[list[ApprovalLog]] = relationship(
        "ApprovalLog",
        back_populates="expense",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ApprovalLog.created_at.desc()",
    )

    # Only composite indexes belong in __table_args__
    __table_args__ = (
        Index("ix_expenses_applicant_status", "applicant_id", "status"),
        Index("ix_expenses_approver_status", "assigned_approver_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Expense id={self.id} amount={self.amount} category={self.category} status={self.status}>"


class CategoryApprover(ExpenseBase, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "category_approvers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory, native_enum=False, length=50),
        unique=True,
        nullable=False,
        index=True,
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationship
    approver: Mapped[User] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CategoryApprover category={self.category} approver_id={self.approver_id}>"
