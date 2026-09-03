import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.core.enums import ApprovalAction
from app.schemas.base import InputModel, OutputModel


class ApproveRequest(InputModel):
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is not None:
            stripped = value.strip()
            return stripped if stripped else None
        return None


class RejectRequest(InputModel):
    reason: str = Field(..., min_length=1)

    @field_validator("reason")
    @classmethod
    def validate_non_empty_reason(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Rejection reason cannot be empty or whitespace only")
        return stripped


class ApprovalLogResponse(OutputModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    actor_id: uuid.UUID
    action: ApprovalAction
    comment: str | None = None
    created_at: datetime
