import logging
from email.message import EmailMessage
import smtplib
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:

        if not settings.email_enabled:
            logger.warning("Email no configurado (falta SMTP o SENDGRID_API_KEY)")
            return False

        if settings.SMTP_HOST and settings.SMTP_USER:
            return EmailService._send_via_smtp(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                reply_to=reply_to,
                from_name=from_name,
            )

        logger.error("No hay configuración de email válida")
        return False

    @staticmethod
    def _send_via_smtp(
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str],
        from_name: Optional[str],
    ) -> bool:
        try:
            msg = EmailMessage()
            msg["From"] = f"{from_name or settings.PROJECT_NAME} <{settings.SMTP_USER}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            if reply_to:
                msg["Reply-To"] = reply_to

            msg.set_content("Tu cliente de correo no soporta HTML.", subtype="plain")
            msg.add_alternative(html_content, subtype="html")

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email enviado correctamente a {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error enviando email SMTP: {e}", exc_info=True)
            return False