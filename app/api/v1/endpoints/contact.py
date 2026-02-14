from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db, get_current_admin, get_client_info
from app.schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactAdmin,
    ContactMarkRead,
    ContactStats
)
from app.services.contact_service import contact_service
from app.tasks.contact_tasks import send_contact_emails, send_admin_reply_email

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit contact form",
    description="Submit a contact form message. Sends automatic confirmation to user and notification to admin."
)
async def submit_contact(
    contact: ContactCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        client_info = get_client_info(request)

        db_contact = contact_service.create_contact(
            db=db,
            contact_in=contact,
            client_info=client_info
        )

        contact_data = {
            "id": db_contact.id,
            "name": db_contact.name,
            "email": db_contact.email,
            "subject": db_contact.subject,
            "message": db_contact.message,
            "timestamp": db_contact.timestamp.isoformat(),
        }

        background_tasks.add_task(send_contact_emails, contact_data)

        return db_contact

    except Exception as e:
        logger.error("Error submitting contact", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting contact message"
        )


@router.get(
    "/messages",
    response_model=List[ContactAdmin],
    summary="Get all contact messages (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_contact_messages(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    return contact_service.get_all(db, skip, limit, unread_only)


@router.get(
    "/messages/{contact_id}",
    response_model=ContactAdmin,
    summary="Get specific contact message",
    dependencies=[Depends(get_current_admin)]
)
async def get_contact_message(
    contact_id: int,
    db: Session = Depends(get_db)
):
    contact = contact_service.get_by_id(db, contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    return contact


@router.patch(
    "/messages/{contact_id}/read",
    response_model=ContactAdmin,
    summary="Mark message as read/unread",
    dependencies=[Depends(get_current_admin)]
)
async def mark_message_read(
    contact_id: int,
    data: ContactMarkRead,
    db: Session = Depends(get_db)
):
    contact = contact_service.mark_as_read(db, contact_id, data.is_read)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    return contact


@router.delete(
    "/messages/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete contact message",
    dependencies=[Depends(get_current_admin)]
)
async def delete_contact_message(
    contact_id: int,
    db: Session = Depends(get_db)
):
    deleted = contact_service.delete_contact(db, contact_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )


@router.post(
    "/messages/{contact_id}/reply",
    summary="Send manual reply to contact (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def reply_to_contact(
    contact_id: int,
    reply_content: str,
    admin_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    contact = contact_service.get_by_id(db, contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    contact_data = {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "subject": contact.subject,
        "message": contact.message,
    }

    background_tasks.add_task(
        send_admin_reply_email,
        contact_data,
        reply_content,
        admin_name
    )

    contact_service.mark_as_read(db, contact_id, True)

    return {
        "message": "Reply sent successfully",
        "contact_id": contact_id,
        "recipient": contact.email
    }


@router.get(
    "/stats",
    response_model=ContactStats,
    summary="Get contact statistics",
    dependencies=[Depends(get_current_admin)]
)
async def get_contact_stats(db: Session = Depends(get_db)):
    return contact_service.get_stats(db)
