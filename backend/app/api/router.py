from fastapi import APIRouter

from app.api.routes import auth, brs, dashboard, health, indicators, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(indicators.router)
api_router.include_router(brs.router)
api_router.include_router(dashboard.router)
