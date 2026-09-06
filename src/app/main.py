from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions.handlers import register_handlers
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")

    expense_settings = get_settings()
    init_db(expense_settings.DATABASE_URL, pool_size=20, max_overflow=10)
    yield

    await close_db()


app = FastAPI(
    title="MVP Expense Approval API",
    version="0.1.0",
    lifespan=lifespan,
)

register_handlers(app)
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
