from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationMarkRead
)
from app.services.notification_service import notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/user/{wallet_address}",
    response_model=List[NotificationResponse],
    summary="Get user notifications"
)
async def get_user_notifications(
    wallet_address: str,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    return notification_service.get_user_notifications(
        db=db,
        wallet_address=wallet_address,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )

@router.get(
    "/user/{wallet_address}/unread-count",
    summary="Get unread notification count"
)
async def get_unread_count(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    count = notification_service.get_unread_count(db, wallet_address)
    return {"unread_count": count}

@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read"
)
async def mark_as_read(
    notification_id: int,
    data: NotificationMarkRead,
    db: Session = Depends(get_db)
):
    notification = notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        read=data.read
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification

@router.post(
    "/user/{wallet_address}/mark-all-read",
    summary="Mark all notifications as read"
)
async def mark_all_read(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    count = notification_service.mark_all_read(db, wallet_address)
    return {"marked_read": count}

@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification"
)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    deleted = notification_service.delete_notification(db, notification_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification (Internal use)"
)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    try:
        return notification_service.create_notification(db, notification)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
