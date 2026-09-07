from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.core.exceptions.app import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import Token, UserCreate


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def register(self, payload: UserCreate) -> tuple[User, Token]:
        """
        Register a new user and return user instance with access token.

        Raises:
            ConflictError: If a user with the same email already exists.
        """
        if await self._user_repo.get_by_email(payload.email):
            raise ConflictError(
                f"A user with email '{payload.email}' already exists."
            )

        hashed = await hash_password(payload.password)
        user = await self._user_repo.create(
            **payload.model_dump(exclude={"password"}),
            hashed_password=hashed,
            roles=[str(UserRole.EMPLOYEE)], # default: employee role
            is_active=True,
        )
        await self._session.commit()

        logger.bind(user_id=str(user.id), email=user.email).info(
            "New user registered"
        )

        token = Token(access_token=create_access_token(str(user.id), user.roles))
        return user, token

    async def login(self, email: str, password: str) -> Token:
        """
        Authenticate user by email and password and return access token.

        Raises:
            AuthenticationError: If credentials are invalid or the account is inactive.
        """
        user = await self._user_repo.get_by_email(email)

        if user is None or not await verify_password(password, user.hashed_password):
            logger.bind(email=email).warning("Failed login attempt")
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            logger.bind(user_id=str(user.id)).warning("Inactive user login attempt")
            raise AuthenticationError("Account is deactivated.")

        logger.bind(user_id=str(user.id), email=email).info("User logged in")
        return Token(access_token=create_access_token(str(user.id), user.roles))

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Retrieve a user by their unique identifier.

        Raises:
            NotFoundError: If no user with the given ID exists.
        """
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise NotFoundError(f"User '{user_id}' not found.")

        user = await self._user_repo.get_by_id(uid)
        if user is None:
            raise NotFoundError(f"User '{user_id}' not found.")
        return user
