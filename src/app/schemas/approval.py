from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from app.core.enums import ApprovalAction
from app.schemas.ai import AIAnalysisResponse
from app.schemas.base import InputModel, OutputModel
from app.schemas.expense import ExpenseResponse


class ApproveRequest(InputModel):
    pass

class RejectRequest(InputModel):
    reason: str = Field(min_length=1)

class ApprovalLogResponse(OutputModel):
    id: uuid.UUID
    expense_id: uuid.UUID
    actor_id: uuid.UUID
    action: ApprovalAction
    comment: str | None = None
    created_at: datetime


class ApprovalClaimResponse(OutputModel):
    expense: ExpenseResponse
    ai_analysis: AIAnalysisResponse
