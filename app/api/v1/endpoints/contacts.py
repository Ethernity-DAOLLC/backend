from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.v1.deps import get_db, get_current_admin
from app.schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactAdmin,
    ContactMarkRead
)
from app.services.contact_service import ContactService
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
        if not contact.ip_address:
            contact.ip_address = request.client.host if request.client else None
        
        if not contact.user_agent:
            contact.user_agent = request.headers.get("user-agent", None)
        db_contact = ContactService.create_contact(db, contact)

        contact_data = {
            "id": db_contact.id,
            "name": db_contact.name,
            "email": db_contact.email,
            "subject": db_contact.subject,
            "message": db_contact.message,
            "timestamp": db_contact.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": db_contact.ip_address
        }
        background_tasks.add_task(send_contact_emails, contact_data)
        
        logger.info(f"✅ Contact message received from {contact.email}")
        
        return db_contact
        
    except Exception as e:
        logger.error(f"❌ Error submitting contact: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar el mensaje de contacto"
        )


@router.get(
    "/messages",
    response_model=List[ContactAdmin],
    summary="Get all contact messages (Admin)",
    description="Retrieve all contact messages - requires admin authentication"
)
async def get_contact_messages(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):
    return ContactService.get_all_contacts(db, skip, limit, unread_only)


@router.get(
    "/messages/{contact_id}",
    response_model=ContactAdmin,
    summary="Get specific contact message"
)
async def get_contact_message(
    contact_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):

    contact = ContactService.get_contact_by_id(db, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje de contacto no encontrado"
        )
    
    return contact

@router.patch(
    "/messages/{contact_id}/read",
    response_model=ContactAdmin,
    summary="Mark message as read/unread"
)
async def mark_message_read(
    contact_id: int,
    data: ContactMarkRead,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):

    contact = ContactService.mark_as_read(db, contact_id, data.is_read)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje de contacto no encontrado"
        )
    
    return contact


@router.delete(
    "/messages/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete contact message"
)
async def delete_contact_message(
    contact_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):

    deleted = ContactService.delete_contact(db, contact_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje de contacto no encontrado"
        )
    
    return None


@router.post(
    "/messages/{contact_id}/reply",
    status_code=status.HTTP_200_OK,
    summary="Send manual reply to contact (Admin)",
    description="Admin sends a manual reply to a contact message"
)
async def reply_to_contact(
    contact_id: int,
    reply_content: str,
    admin_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):

    contact = ContactService.get_contact_by_id(db, contact_id)
    
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensaje de contacto no encontrado"
        )

    contact_data = {
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "subject": contact.subject,
        "message": contact.message
    }

    background_tasks.add_task(
        send_admin_reply_email,
        contact_data,
        reply_content,
        admin_name
    )

    ContactService.mark_as_read(db, contact_id, True)
    
    logger.info(f"✅ Reply scheduled for contact {contact_id}")
    
    return {
        "message": "Respuesta enviada correctamente",
        "contact_id": contact_id,
        "recipient": contact.email
    }


@router.get(
    "/stats",
    summary="Get contact statistics"
)
async def get_contact_stats(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_admin)
):

    total = len(ContactService.get_all_contacts(db, limit=10000))
    unread = ContactService.get_unread_count(db)
    recent = len(ContactService.get_recent_contacts(db, days=7))
    
    return {
        "total_messages": total,
        "unread_messages": unread,
        "messages_last_7_days": recent,
        "read_percentage": round((total - unread) / total * 100, 2) if total > 0 else 0
    }