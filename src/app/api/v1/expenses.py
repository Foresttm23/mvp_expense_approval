"""Expense claim endpoints — employee-facing operations."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentEmployee, DbSession
from app.core.enums import ExpenseStatus
from app.schemas.base import PaginatedResponse
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["Expenses"])

def get_expense_service(db: DbSession) -> ExpenseService:
    return ExpenseService(db)


ExpenseServiceDep = Annotated[ExpenseService, Depends(get_expense_service)]

@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new expense claim"
)
async def submit_expense(
    payload: ExpenseCreate,
    current_user: CurrentEmployee,
    service: ExpenseServiceDep,
) -> ExpenseResponse:
    expense = await service.create_expense(
        applicant_id=current_user.id,
        payload=payload,
    )
    return ExpenseResponse.model_validate(expense)


@router.get(
    "",
    response_model=PaginatedResponse[ExpenseResponse],
    summary="List authenticated user's expense claims",
)
async def list_expenses(
    current_user: CurrentEmployee,
    service: ExpenseServiceDep,
    expense_status: ExpenseStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[ExpenseResponse]:
    offset = (page - 1) * page_size
    items, total = await service.get_applicant_expenses(
        applicant_id=current_user.id,
        status=expense_status,
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
    response_model=ExpenseResponse,
    summary="Get details of a specific expense claim",
    description="Returns full details of a single expense claim. Only accessible by the original applicant.",
)
async def get_expense(
    expense_id: uuid.UUID,
    current_user: CurrentEmployee,
    service: ExpenseServiceDep,
) -> ExpenseResponse:
    expense = await service.get_expense_for_applicant(
        expense_id=expense_id,
        applicant_id=current_user.id,
    )
    return ExpenseResponse.model_validate(expense)


@router.post(
    "/{expense_id}/withdraw",
    response_model=ExpenseResponse,
    summary="Withdraw a pending expense claim",
    description=(
        "Transitions the claim from **pending** → **withdrawn**. "
        "Only the original applicant can withdraw, and only while the claim is still pending."
    ),
)
async def withdraw_expense(
    expense_id: uuid.UUID,
    current_user: CurrentEmployee,
    service: ExpenseServiceDep,
) -> ExpenseResponse:
    expense = await service.withdraw_expense(
        expense_id=expense_id,
        applicant_id=current_user.id,
    )
    return ExpenseResponse.model_validate(expense)
