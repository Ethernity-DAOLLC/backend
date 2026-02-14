from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db, get_current_admin, get_client_info
from app.schemas.user import (
    EmailAssociation,
    UserResponse,
    UserAdmin,
    UserCreate,
    UserUpdate
)
from app.services.user_service import user_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/email",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Associate email with wallet"
)
async def associate_email(
    data: EmailAssociation,
    db: Session = Depends(get_db)
):
    try:
        user = user_service.associate_email(
            db=db,
            wallet_address=data.address,
            email=data.email,
            accepts_marketing=data.accepts_marketing,
            accepts_notifications=data.accepts_notifications
        )
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        client_info = get_client_info(request)
        user = user_service.create_user(db, user_data, client_info)
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/wallet/{wallet_address}",
    response_model=UserResponse,
    summary="Get user by wallet"
)
async def get_user_by_wallet(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    user = user_service.get_by_wallet(db, wallet_address)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post(
    "/login/{wallet_address}",
    response_model=UserResponse,
    summary="Update last login"
)
async def user_login(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    user = user_service.update_last_login(db, wallet_address)
    if not user:
        user = user_service.create_user(
            db,
            UserCreate(wallet_address=wallet_address)
        )
    
    return user

@router.get(
    "/",
    response_model=List[UserAdmin],
    summary="Get all users (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return user_service.get_all_users(db, skip, limit)

@router.get(
    "/mailing-list",
    response_model=List[UserAdmin],
    summary="Get mailing list (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_mailing_list(
    accepts_marketing: bool = True,
    email_verified: bool = False,
    db: Session = Depends(get_db)
):
    return user_service.get_users_for_mailing(
        db,
        accepts_marketing=accepts_marketing,
        email_verified=email_verified
    )

@router.get(
    "/search",
    response_model=List[UserAdmin],
    summary="Search users (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def search_users(
    q: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return user_service.search_users(db, q, skip, limit)

@router.patch(
    "/{user_id}",
    response_model=UserAdmin,
    summary="Update user (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    user = user_service.update_user(db, user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
