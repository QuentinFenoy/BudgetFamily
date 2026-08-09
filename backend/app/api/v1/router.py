"""Agrège tous les routers de la version v1 de l'API."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.budgeting import router as budgeting_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.savings import router as savings_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(budgeting_router)
api_router.include_router(savings_router)

# À venir au fil des modules suivants :
# api_router.include_router(reports_router)
# api_router.include_router(billing_router)
# api_router.include_router(auth_router)
