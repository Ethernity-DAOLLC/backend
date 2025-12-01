import logging
from typing import Dict
from app.core.config import settings
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

def send_contact_emails(contact_data: Dict):
    logger.info(f"📧 Processing emails for contact {contact_data['id']}")
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("⚠️ SENDGRID_API_KEY not configured - skipping emails")
        return
    
    try:
        user_subject = "Hemos recibido tu mensaje"
        user_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">¡Gracias por contactarnos, {contact_data['name']}!</h2>
                <p>Hemos recibido tu mensaje y te responderemos lo antes posible.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Resumen de tu mensaje:</h3>
                    <p><strong>Asunto:</strong> {contact_data['subject']}</p>
                    <p><strong>Mensaje:</strong><br>{contact_data['message'][:200]}...</p>
                    <p><strong>Fecha:</strong> {contact_data['timestamp']}</p>
                </div>
                
                <p>Nuestro equipo revisará tu mensaje y te contactará por este email: <strong>{contact_data['email']}</strong></p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #6b7280;">
                    Este es un mensaje automático. Por favor no respondas a este email.
                </p>
            </div>
        </body>
        </html>
        """

        EmailService.send_email(
            to_email=contact_data['email'],
            subject=user_subject,
            html_content=user_html
        )

        if settings.ADMIN_EMAIL:
            admin_subject = f"Nuevo contacto: {contact_data['subject'][:50]}"
            admin_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc2626;">🔔 Nuevo mensaje de contacto</h2>
                    
                    <div style="background-color: #fef2f2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0;">
                        <p><strong>De:</strong> {contact_data['name']}</p>
                        <p><strong>Email:</strong> {contact_data['email']}</p>
                        <p><strong>Asunto:</strong> {contact_data['subject']}</p>
                        <p><strong>IP:</strong> {contact_data.get('ip_address', 'N/A')}</p>
                        <p><strong>Timestamp:</strong> {contact_data['timestamp']}</p>
                    </div>
                    
                    <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px;">
                        <h3>Mensaje:</h3>
                        <p style="white-space: pre-wrap;">{contact_data['message']}</p>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <a href="http://localhost:8000/api/v1/contact/messages/{contact_data['id']}" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Ver en el panel admin
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
            
            EmailService.send_email(
                to_email=settings.ADMIN_EMAIL,
                subject=admin_subject,
                html_content=admin_html
            )
        
        logger.info(f"✅ Emails sent successfully for contact {contact_data['id']}")
        
    except Exception as e:
        logger.error(f"❌ Error sending contact emails: {e}", exc_info=True)


def send_admin_reply_email(contact_data: Dict, reply_content: str, admin_name: str):
    logger.info(f"📧 Sending admin reply to {contact_data['email']}")
    
    if not settings.SENDGRID_API_KEY:
        logger.warning("⚠️ SENDGRID_API_KEY not configured - skipping email")
        return
    
    try:
        subject = f"Re: {contact_data['subject']}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Respuesta de {admin_name}</h2>
                
                <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="white-space: pre-wrap;">{reply_content}</p>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                
                <div style="background-color: #f9fafb; padding: 15px; border-radius: 8px;">
                    <p style="font-size: 14px; color: #6b7280; margin: 0;">
                        <strong>Tu mensaje original:</strong>
                    </p>
                    <p style="margin-top: 10px;">{contact_data['message']}</p>
                </div>
                
                <p style="margin-top: 30px;">
                    Si tienes más preguntas, no dudes en responder a este email.
                </p>
                
                <p style="font-size: 12px; color: #6b7280; margin-top: 30px;">
                    Saludos,<br>
                    Equipo de {settings.PROJECT_NAME}
                </p>
            </div>
        </body>
        </html>
        """
        
        EmailService.send_email(
            to_email=contact_data['email'],
            subject=subject,
            html_content=html,
            reply_to=settings.ADMIN_EMAIL
        )
        
        logger.info(f"✅ Admin reply sent to {contact_data['email']}")
        
    except Exception as e:
        logger.error(f"❌ Error sending admin reply: {e}", exc_info=True)