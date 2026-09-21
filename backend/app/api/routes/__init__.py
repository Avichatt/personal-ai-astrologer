"""API routes package."""

from fastapi import APIRouter

from app.api.routes.analysis import router as analysis_router
from app.api.routes.auth import router as auth_router
from app.api.routes.birth_profiles import router as birth_profiles_router
from app.api.routes.charts import router as charts_router
from app.api.routes.events import router as events_router
from app.api.routes.transits import router as transits_router
from app.api.routes.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(birth_profiles_router)
api_router.include_router(charts_router)
api_router.include_router(transits_router)
api_router.include_router(events_router)
api_router.include_router(analysis_router)

