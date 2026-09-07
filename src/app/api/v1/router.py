# Central aggregation router for API v1.

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import approvals, auth, expenses

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(expenses.router)
api_v1_router.include_router(approvals.router)
