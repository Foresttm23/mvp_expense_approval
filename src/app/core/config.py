from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ExpenseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


@lru_cache
def get_settings() -> ExpenseSettings:
    return ExpenseSettings()