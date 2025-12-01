import logging
from app.core.config import settings
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

async def send_new_contact_notification(contact_data: dict):
    subject = f"Nuevo mensaje de contacto: {contact_data['subject'][:50]}..."
    html = f"""
    <h2>Nuevo mensaje en el Fondo de Retiro</h2>
    <p><strong>De:</strong> {contact_data['name']} ({contact_data['email']})</p>
    {f"<p><strong>Wallet:</strong> {contact_data.get('wallet_address', 'No conectado')}</p>" if contact_data.get('wallet_address') else ""}
    <p><strong>Asunto:</strong> {contact_data['subject']}</p>
    <hr>
    <p>{contact_data['message'].replace(chr(10), '<br>')}</p>
    <br>
    <p><a href="https://tu-dominio.com/admin/contact">Ir al panel de mensajes →</a></p>
    """

    try:
        await EmailService.send_email(
            to_email="soporte@tu-fondo.com",
            subject=subject,
            html_content=html
        )
        logger.info(f"Email enviado para contacto de {contact_data['email']}")
    except Exception as e:
        logger.error(f"Error enviando email de contacto: {e}")