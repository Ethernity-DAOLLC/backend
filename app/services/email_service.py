import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email_async(
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:

        if not settings.SMTP_HOST:
            logger.warning("⚠️ SMTP_HOST not configured - email sending disabled")
            return False
        
        if not settings.EMAIL_FROM:
            logger.error("❌ EMAIL_FROM not configured")
            return False
        
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{from_name or settings.PROJECT_NAME} <{from_email or settings.EMAIL_FROM}>"
            message['To'] = to_email
            
            if reply_to:
                message['Reply-To'] = reply_to
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)

            smtp_config = {
                'hostname': settings.SMTP_HOST,
                'port': settings.SMTP_PORT,
                'use_tls': settings.SMTP_TLS,
            }

            if settings.SMTP_USER:
                smtp_config['username'] = settings.SMTP_USER
                smtp_config['password'] = settings.SMTP_PASSWORD or ''

            await aiosmtplib.send(
                message,
                **smtp_config
            )
            
            logger.info(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email to {to_email}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        EmailService.send_email_async(
                            to_email=to_email,
                            subject=subject,
                            html_content=html_content,
                            from_email=from_email,
                            from_name=from_name,
                            reply_to=reply_to
                        )
                    )
                    return future.result()
            except RuntimeError:
                return asyncio.run(
                    EmailService.send_email_async(
                        to_email=to_email,
                        subject=subject,
                        html_content=html_content,
                        from_email=from_email,
                        from_name=from_name,
                        reply_to=reply_to
                    )
                )
        except Exception as e:
            logger.error(f"❌ Error in sync email wrapper: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def send_bulk_email_async(
        to_emails: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> dict:
        results = {"success": 0, "failed": 0, "total": len(to_emails)}
        
        if not settings.SMTP_HOST:
            logger.error("❌ SMTP not configured for bulk email")
            results["failed"] = len(to_emails)
            return results

        tasks = []
        for email in to_emails:
            task = EmailService.send_email_async(
                to_email=email,
                subject=subject,
                html_content=html_content,
                from_email=from_email
            )
            tasks.append(task)
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results_list:
            if isinstance(result, bool) and result:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        logger.info(f"📊 Bulk email results: {results}")
        return results
    
    @staticmethod
    def send_bulk_email(
        to_emails: List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None
    ) -> dict:

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        EmailService.send_bulk_email_async(
                            to_emails=to_emails,
                            subject=subject,
                            html_content=html_content,
                            from_email=from_email
                        )
                    )
                    return future.result()
            except RuntimeError:
                return asyncio.run(
                    EmailService.send_bulk_email_async(
                        to_emails=to_emails,
                        subject=subject,
                        html_content=html_content,
                        from_email=from_email
                    )
                )
        except Exception as e:
            logger.error(f"❌ Error in bulk email wrapper: {e}", exc_info=True)
            return {"success": 0, "failed": len(to_emails), "total": len(to_emails)}
    
    @staticmethod
    def send_contact_notification(
        contact_name: str,
        contact_email: str,
        contact_subject: str,
        contact_message: str
    ) -> bool:
        admin_emails = settings.ADMIN_EMAILS
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ background-color: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 5px; }}
                .field {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #4F46E5; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📧 Nuevo mensaje de contacto</h2>
                </div>
                <div class="content">
                    <div class="field">
                        <span class="label">Nombre:</span> {contact_name}
                    </div>
                    <div class="field">
                        <span class="label">Email:</span> {contact_email}
                    </div>
                    <div class="field">
                        <span class="label">Asunto:</span> {contact_subject}
                    </div>
                    <div class="field">
                        <span class="label">Mensaje:</span>
                        <p>{contact_message}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático de {settings.PROJECT_NAME}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = True
        for admin_email in admin_emails:
            result = EmailService.send_email(
                to_email=admin_email,
                subject=f"Nuevo contacto: {contact_subject}",
                html_content=html_content,
                reply_to=contact_email
            )
            if not result:
                success = False
        
        return success