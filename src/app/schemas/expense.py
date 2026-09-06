import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import ConfigDict, Field, field_validator

from app.core.enums import ExpenseCategory, ExpenseStatus
from app.schemas.base import InputModel, OutputModel


class ExpenseBase(InputModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    category: ExpenseCategory
    description: str = Field(min_length=1)
    expense_date: date
    payment_details: str = Field(min_length=1, max_length=500)

    @field_validator("description", "payment_details")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or whitespace only")
        return stripped


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(OutputModel, ExpenseBase):
    id: uuid.UUID
    applicant_id: uuid.UUID
    status: ExpenseStatus
    assigned_approver_id: uuid.UUID
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ExpenseFilter(InputModel):
    status: ExpenseStatus | None = None
    category: ExpenseCategory | None = None
    from_date: date | None = None
    to_date: date | None = None


class CategoryApproverResponse(OutputModel):
    id: uuid.UUID
    category: ExpenseCategory
    approver_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class CategoryApproverCreate(InputModel):
    category: ExpenseCategory
    approver_id: uuid.UUID
