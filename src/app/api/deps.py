from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from functools import cache
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai_provider import LLMProvider
from app.core.config import ExpenseSettings, get_settings
from app.core.database import db_session_manager
from app.core.enums import UserRole
from app.core.exceptions.app import NotFoundError, UnauthorizedActionError
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.services.ai_service import AIService
from app.services.providers.gemini_provider import GeminiProvider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with db_session_manager.session() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]


TokenDep = Annotated[str, Depends(oauth2_scheme)]

async def get_current_user(
    token: TokenDep,
    db: DbSession,
) -> User:
    """
    Decode the JWT and return the associated ``User``.

    Raises:
        UnauthorizedActionError: If the token is expired, malformed, or the
            embedded subject does not correspond to an existing active user.
    """
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise UnauthorizedActionError("Token payload is missing subject.")
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        raise UnauthorizedActionError("Token has expired.")
    except jwt.InvalidTokenError as exc:
        logger.debug("Invalid token: {}", exc)
        raise UnauthorizedActionError("Invalid authentication token.")

    user_repo = UserRepository(db)
    try:
        user = await user_repo.get_by_id(uuid.UUID(user_id))
    except (ValueError, TypeError):
        raise UnauthorizedActionError("Could not validate credentials.")

    if user is None:
        raise NotFoundError("User not found.")

    if not user.is_active:
        raise UnauthorizedActionError("Account is deactivated.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(role: str):
    async def _guard(current_user: CurrentUser) -> User:
        if role not in (current_user.roles or []):
            logger.bind(
                user_id=str(current_user.id),
                required_role=role,
                user_roles=current_user.roles,
            ).warning("Role check failed")
            raise UnauthorizedActionError(
                f"You need the '{role}' role to access this resource."
            )
        return current_user

    return _guard


CurrentApprover = Annotated[User, Depends(require_role(UserRole.APPROVER))]
CurrentEmployee = Annotated[User, Depends(require_role(UserRole.EMPLOYEE))]


@cache
def _build_ai_provider(settings: ExpenseSettings) -> LLMProvider:
    """
    Build and cache the LLM provider for the lifetime of the process.

    If a new LLM provider is needed, add a new LLMProvider implementation
    and update this method to return the new provider.
    """
    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.AI_MODEL_NAME,
    )


def get_ai_service(
    settings: Annotated[ExpenseSettings, Depends(get_settings)],
) -> AIService:
    provider = _build_ai_provider(settings)
    return AIService(provider=provider, timeout=settings.AI_TIMEOUT_SECONDS)


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
