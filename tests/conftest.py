from __future__ import annotations

import os

from app.core.database import db_session_manager, init_db
from app.core.seed import seed_database
from app.models.base import Base

# Override DATABASE_URL before importing the app so pydantic-settings picks up
# localhost instead of the Docker-internal 'db' hostname from .env.
# setdefault: a DATABASE_URL already in the shell environment always wins.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
)

from app.core.config import get_settings

get_settings.cache_clear()

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

BASE_URL = "http://test"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_test_db():
    settings = get_settings()
    init_db(settings.DATABASE_URL)

    async with db_session_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    await seed_database()

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """
    Async HTTP client wired to the FastAPI ASGI app.

    The lifespan context manager fires startup (init_db) and shutdown
    (close_db) so the DB session manager is fully initialised for each test.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE_URL,
        timeout=30.0,
    ) as ac, app.router.lifespan_context(app):
        yield ac
