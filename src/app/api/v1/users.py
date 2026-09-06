"""User management endpoints — approver discovery and user administration."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/approvers",
    response_model=list[UserResponse],
    summary="List all users with the approver role"
)
async def list_approvers(
    _current_user: CurrentUser,
    db: DbSession,
) -> list[UserResponse]:
    result = await db.execute(
        select(User).where(
            User.roles.contains([UserRole.APPROVER]),
            User.is_active.is_(True),
        )
    )
    approvers = list(result.scalars().all())
    return [UserResponse.model_validate(u) for u in approvers]
