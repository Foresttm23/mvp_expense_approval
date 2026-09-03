from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.exceptions.handlers import register_handlers
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")

    expense_settings = get_settings()
    init_db(expense_settings.DATABASE_URL, pool_size=20, max_overflow=10)
    yield
    logger.info("Shutdown")

    await close_db()


app = FastAPI(
    title="MVP Expense Approval API",
    version="0.1.0",
    lifespan=lifespan,
)

register_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="[IP_ADDRESS]", port=8000)
