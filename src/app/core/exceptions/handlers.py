from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions import AppException


def register_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        logger.bind(
            status_code=exc.status_code,
            path=request.url.path,
        ).warning("Handled domain error: {msg}", msg=exc.message)

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
