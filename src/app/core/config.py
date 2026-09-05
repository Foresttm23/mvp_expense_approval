from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    DEFAULT_CATEGORY_APPROVERS: dict[str, str] = {
        "OFFICE": "approver_office@example.com",
        "TRAVEL": "approver_travel@example.com",
        "CLIENT_ENTERTAINMENT": "approver_entertainment@example.com",
        "SOFTWARE_SUBSCRIPTIONS": "approver_software@example.com",
        "OTHER": "approver_general@example.com",
    }


@lru_cache
def get_settings() -> ExpenseSettings:
    return ExpenseSettings()
