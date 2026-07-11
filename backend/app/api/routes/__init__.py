"""Aggregate API router mounting every route module under /api."""

from fastapi import APIRouter

from app.api.routes import (
    admin,
    alerts,
    cases,
    customers,
    dashboard,
    merchants,
    risk_scores,
    search,
    transactions,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(dashboard.router)
api_router.include_router(customers.router)
api_router.include_router(transactions.router)
api_router.include_router(merchants.router)
api_router.include_router(alerts.router)
api_router.include_router(cases.router)
api_router.include_router(risk_scores.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
