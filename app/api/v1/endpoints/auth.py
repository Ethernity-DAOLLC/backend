from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import timedelta
import logging

from app.core.config import settings
from app.core.jwt import jwt_manager
from app.api.deps import get_db
from app.services.user_service import user_service

logger = logging.getLogger(__name__)
router = APIRouter()

class WalletAuthRequest(BaseModel):
    wallet_address: str = Field(..., min_length=42, max_length=42)
    signature: str = Field(..., description="Firma del mensaje")
    message: str = Field(..., description="Mensaje firmado")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminLoginRequest(BaseModel):
    email: str
    password: str

@router.post(
    "/wallet/login",
    response_model=TokenResponse,
    summary="Login con wallet Web3"
)
async def wallet_login(
    auth_data: WalletAuthRequest,
    db: Session = Depends(get_db)
):
    
    # TODO: Aquí deberías verificar la firma criptográficamente
    # from eth_account.messages import encode_defunct
    # from web3 import Web3
    # 
    # message_hash = encode_defunct(text=auth_data.message)
    # recovered_address = w3.eth.account.recover_message(
    #     message_hash,
    #     signature=auth_data.signature
    # )
    # 
    # if recovered_address.lower() != auth_data.wallet_address.lower():
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Por ahora, asumimos que la firma es válida
    wallet_address = auth_data.wallet_address.lower()
    
    try:
        user = user_service.get_by_wallet(db, wallet_address)
        
        if not user:
            from app.schemas.user import UserCreate
            user = user_service.create_user(
                db,
                UserCreate(wallet_address=wallet_address)
            )
        else:
            user_service.update_last_login(db, wallet_address)
        access_token = jwt_manager.create_access_token(
            data={
                "sub": wallet_address,
                "user_id": user.id,
                "role": "user"
            }
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            data={
                "sub": wallet_address,
                "user_id": user.id,
                "role": "user"
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token"
)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):

    try:
        payload = jwt_manager.verify_refresh_token(refresh_data.refresh_token)
        wallet_address = payload.get("sub")
        user_id = payload.get("user_id")
        role = payload.get("role", "user")
        
        if not wallet_address or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = user_service.get(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        access_token = jwt_manager.create_access_token(
            data={
                "sub": wallet_address,
                "user_id": user_id,
                "role": role
            }
        )
        new_refresh_token = jwt_manager.create_refresh_token(
            data={
                "sub": wallet_address,
                "user_id": user_id,
                "role": role
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post(
    "/admin/login",
    response_model=TokenResponse,
    summary="Login de administrador"
)
async def admin_login(login_data: AdminLoginRequest):
    if (
        login_data.email == settings.ADMIN_EMAIL and 
        login_data.password == settings.ADMIN_PASSWORD
    ):
        access_token = jwt_manager.create_access_token(
            data={
                "sub": login_data.email,
                "role": "admin"
            },
            expires_delta=timedelta(hours=8)  # Admins: 8 horas
        )
        
        refresh_token = jwt_manager.create_refresh_token(
            data={
                "sub": login_data.email,
                "role": "admin"
            }
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=8 * 60 * 60  # 8 horas en segundos
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

@router.post("/logout", summary="Logout (placeholder)")
async def logout():
    return {
        "message": "Logout successful",
        "instruction": "Remove tokens from client storage"
    }