from fastapi import APIRouter
from app.api.v1.endpoints import contact
from app.api.v1.endpoints import users, auth

# from app.api.v1.endpoints import auth, users, contributions, etc.

api_router = APIRouter()

@api_router.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "message": "API funcionando correctamente"
    }

api_router.include_router(
    contact.router,
    prefix="/contact",
    tags=["contact"]
)

# Rutas protegidas (descomentar cuando las implementes)
# api_router.include_router(
#     auth.router,
#     prefix="/auth",
#     tags=["authentication"]
# )
# api_router.include_router(
#     users.router,
#     prefix="/users",
#     tags=["users"]
# )