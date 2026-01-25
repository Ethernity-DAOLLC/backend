from fastapi import APIRouter
from app.api.v1.endpoints.contact import router as contact_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.stats import router as stats_router
from app.api.v1.endpoints.survey import router as survey_router
from app.api.v1.endpoints.funds import router as funds_router
from app.api.v1.endpoints.tokens import router as tokens_router
from app.api.v1.endpoints.governance import router as governance_router
from app.api.v1.endpoints.protocols import router as protocols_router
from app.api.v1.endpoints.treasury import router as treasury_router
from app.api.v1.endpoints.preferences import router as preferences_router
from app.api.v1.endpoints.blockchain import router as blockchain_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.notifications import router as notifications_router

api_router = APIRouter()
@api_router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Ethernity DAO API v1 - Operational",
        "version": "1.0.0"
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
    prefix="/surveys",
    tags=["survey"]
)

api_router.include_router(
    funds_router,
    prefix="/funds",
    tags=["personal-funds"]
)

api_router.include_router(
    tokens_router,
    prefix="/tokens",
    tags=["geras-token"]
)

api_router.include_router(
    governance_router,
    prefix="/governance",
    tags=["governance"]
)

api_router.include_router(
    protocols_router,
    prefix="/protocols",
    tags=["defi-protocols"]
)

api_router.include_router(
    treasury_router,
    prefix="/treasury",
    tags=["treasury"]
)

api_router.include_router(
    preferences_router,
    prefix="/preferences",
    tags=["user-preferences"]
)

api_router.include_router(
    blockchain_router,
    prefix="/blockchain",
    tags=["blockchain"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["notifications"]
)
