from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserSeedConfig(BaseModel):
    email: str
    name: str
    password: str = "password123"
    roles: list[str] = Field(default_factory=lambda: ["approver"])


class ExpenseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/expense_db"
    )
    APP_ENV: str = "development"

    # JWT / Auth
    SECRET_KEY: str = "my_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI Advisory
    GEMINI_API_KEY: str | None = None
    AI_MODEL_NAME: str = "gemini-2.0-flash"
    AI_TIMEOUT_SECONDS: float = 5.0

    # Category to Approver Mapping Configuration
    DEFAULT_CATEGORY_APPROVERS: dict[str, UserSeedConfig] = {
        "OFFICE": UserSeedConfig(
            email="approver_office@example.com",
            name="Approver Office",
            password="password123",
            roles=["approver"],
        ),
        "TRAVEL": UserSeedConfig(
            email="approver_travel@example.com",
            name="Approver Travel",
            password="password123",
            roles=["approver"],
        ),
        "CLIENT_ENTERTAINMENT": UserSeedConfig(
            email="approver_entertainment@example.com",
            name="Approver Entertainment",
            password="password123",
            roles=["approver"],
        ),
        "SOFTWARE_SUBSCRIPTIONS": UserSeedConfig(
            email="approver_software@example.com",
            name="Approver Software",
            password="password123",
            roles=["approver"],
        ),
        "OTHER": UserSeedConfig(
            email="approver_general@example.com",
            name="Approver General",
            password="password123",
            roles=["employee", "approver"],
        ),
    }

    # Additional Test Users
    DEFAULT_TEST_USERS: list[UserSeedConfig] = [
        UserSeedConfig(
            email="employee@example.com",
            name="Standard Employee",
            password="password123",
            roles=["employee"],
        ),
        UserSeedConfig(
            email="manager@example.com",
            name="Dual Role Manager",
            password="password123",
            roles=["employee", "approver"],
        ),
    ]


@lru_cache
def get_settings() -> ExpenseSettings:
    return ExpenseSettings()
