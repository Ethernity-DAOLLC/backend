from fastapi import APIRouter

from app.api.v1.endpoints.contact import router as contact_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.stats import router as stats_router
from app.api.v1.endpoints.survey import router as survey_router

api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "API v1 funcionando correctamente"
    }

api_router.include_router(
    contact_router,
    prefix="/contact",
    tags=["contact"]
)

api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    stats_router,
    prefix="/stats",
    tags=["admin-stats"]
)

api_router.include_router(
    survey_router,
    prefix="/survey",
    tags=["survey"]
)

