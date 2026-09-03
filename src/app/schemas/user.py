import uuid
from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core.enums import UserRole
from app.schemas.base import InputModel, OutputModel


class UserBase(InputModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    roles: list[str] = Field(default_factory=lambda: [UserRole.EMPLOYEE.value])
    is_active: bool = True

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, roles: list[str]) -> list[str]:
        valid_roles = {r.value for r in UserRole}
        if not roles:
            raise ValueError("User must have at least one role assigned")
        for role in roles:
            if role not in valid_roles:
                raise ValueError(
                    f"Invalid role: '{role}'. Allowed roles are {sorted(valid_roles)}"
                )
        return sorted(set(roles))


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


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
