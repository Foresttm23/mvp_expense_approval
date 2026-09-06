from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import AIServiceDep, CurrentApprover, DbSession
from app.schemas.ai import AIAnalysisResponse
from app.schemas.approval import ApprovalClaimResponse, RejectRequest
from app.schemas.base import PaginatedResponse
from app.schemas.expense import ExpenseResponse
from app.services.approval_service import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals"])


def get_approval_service(db: DbSession) -> ApprovalService:
    return ApprovalService(db)


ApprovalServiceDep = Annotated[ApprovalService, Depends(get_approval_service)]


@router.get(
    "/queue",
    response_model=PaginatedResponse[ExpenseResponse],
    summary="List pending claims assigned to the current approver"
)
async def get_queue(
    current_approver: CurrentApprover,
    service: ApprovalServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ExpenseResponse]:
    offset = (page - 1) * page_size
    items, total = await service.get_queue(
        approver_id=current_approver.id,
        offset=offset,
        limit=page_size,
    )
    return PaginatedResponse[ExpenseResponse](
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{expense_id}",
    response_model=ApprovalClaimResponse,
    summary="Review a claim — includes AI advisory analysis"
)
async def review_claim(
    expense_id: uuid.UUID,
    current_approver: CurrentApprover,
    service: ApprovalServiceDep,
    ai_service: AIServiceDep,
) -> ApprovalClaimResponse:
    expense = await service.get_expense_for_approver(
        expense_id=expense_id,
        approver_id=current_approver.id,
    )

    ai_analysis: AIAnalysisResponse = await ai_service.analyse_expense(expense)

    return ApprovalClaimResponse(
        expense=ExpenseResponse.model_validate(expense),
        ai_analysis=ai_analysis,
    )


@router.post(
    "/{expense_id}/approve",
    response_model=ExpenseResponse,
    summary="Approve a pending expense claim"
)
async def approve_claim(
    expense_id: uuid.UUID,
    current_approver: CurrentApprover,
    service: ApprovalServiceDep,
) -> ExpenseResponse:
    expense = await service.approve_expense(
        expense_id=expense_id,
        approver_id=current_approver.id,
    )
    return ExpenseResponse.model_validate(expense)


@router.post(
    "/{expense_id}/reject",
    response_model=ExpenseResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject a pending expense claim",
)
async def reject_claim(
    expense_id: uuid.UUID,
    payload: RejectRequest,
    current_approver: CurrentApprover,
    service: ApprovalServiceDep,
) -> ExpenseResponse:
    expense = await service.reject_expense(
        expense_id=expense_id,
        approver_id=current_approver.id,
        reason=payload.reason,
    )
    return ExpenseResponse.model_validate(expense)
