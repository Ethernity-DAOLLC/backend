import logging
from typing import Optional, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service usando SendGrid
    IMPORTANTE: Métodos sync para usar con BackgroundTasks
    """
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:

        if not settings.SENDGRID_API_KEY:
            logger.warning("⚠️ SENDGRID_API_KEY not configured")
            return False
        
        if not settings.EMAIL_FROM:
            logger.error("❌ EMAIL_FROM not configured")
            return False
        
        try:
            from_email_obj = Email(
                email=from_email or settings.EMAIL_FROM,
                name=from_name or settings.PROJECT_NAME
            )
            
            to_email_obj = To(to_email)
            content = Content("text/html", html_content)
            
            mail = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject,
                html_content=content
            )
            
            if reply_to:
                mail.reply_to = Email(reply_to)
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(mail)
            
            logger.info(f"✅ Email sent to {to_email} - Status: {response.status_code}")
            return response.status_code in [200, 201, 202]
            
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def send_bulk_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> dict:
        results = {"success": 0, "failed": 0, "total": len(to_emails)}
        
        for email in to_emails:
            success = EmailService.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                from_email=from_email
            )
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"📊 Bulk email results: {results}")
        return results