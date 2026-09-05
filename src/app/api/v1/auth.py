from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserCreate,
    db: DbSession,
) -> Token:
    service = AuthService(db)
    _user, token = await service.register(payload)
    return token


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with email + password (OAuth2 form)",
)
async def login(
    form_data: OAuth2Form,
    db: DbSession,
) -> Token:
    service = AuthService(db)
    token = await service.login(email=form_data.username, password=form_data.password)
    return token


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user's profile",
)
async def me(current_user: CurrentUser) -> User:
    return current_user
