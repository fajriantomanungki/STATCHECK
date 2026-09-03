from fastapi import APIRouter

from app.api.routes import approvals, auth, brs, checks, dashboard, documents, health, indicators, releases, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(indicators.router)
api_router.include_router(brs.router)
api_router.include_router(documents.router)
api_router.include_router(checks.router)
api_router.include_router(approvals.router)
api_router.include_router(releases.router)
api_router.include_router(dashboard.router)
