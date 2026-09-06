import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.core.enums import UserRole
from app.schemas.base import InputModel, OutputModel


class UserBase(InputModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    roles: list[UserRole] = Field(
        min_length=1,
        default_factory=lambda: [UserRole.EMPLOYEE],
    )
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field( min_length=8, max_length=128)


class UserResponse(OutputModel, UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class Token(OutputModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(InputModel):
    sub: str | None = None
    roles: list[str] = Field(default_factory=list)
    exp: int | None = None
