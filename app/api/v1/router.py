from fastapi import APIRouter
from app.api.v1.endpoints import contact

api_router = APIRouter()
api_router.include_router(
    contact.router,
    prefix="/contact",
    tags=["contact"]
)
# from app.api.v1.endpoints import users, auth, health, etc.

@api_router.get("/health")                                # prueba
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente!"}