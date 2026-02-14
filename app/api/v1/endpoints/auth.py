from fastapi import APIRouter, HTTPException, status
from app.core.config import settings

router = APIRouter()
@router.post("/admin/login")
async def admin_login(email: str, password: str):
    if (
        email == settings.ADMIN_EMAIL and 
        password == settings.ADMIN_PASSWORD and 
        settings.ENVIRONMENT == "development"
    ):
        return {"access_token": settings.ADMIN_TOKEN}
    
    raise HTTPException(status_code=401, detail="Credenciales inválidas")