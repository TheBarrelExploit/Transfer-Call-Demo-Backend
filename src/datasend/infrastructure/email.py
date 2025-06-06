# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import BackgroundTasks
from pydantic import EmailStr, BaseModel
from typing import List, Optional, Dict, Any
from src.shared.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


class EmailSchema(BaseModel):
    email_to: List[EmailStr]  # Destinatario(s)
    subject: str
    body: str
    attachments: Optional[List[Dict[str, Any]]] = None


# Cuenta con Configuración que asegura compatibilidad con Gmail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
)


async def send_email_background(background_tasks: BackgroundTasks, email: EmailSchema):
    try:
        message = MessageSchema(
            subject=email.subject,
            recipients=email.email_to,
            body=email.body,
            subtype="html",
            attachments=email.attachments,
        )
        fm = FastMail(conf)
        background_tasks.add_task(fm.send_message, message)

        # await fm.send_message(message)
        logger.info(f"Email enviado exitosamente a {email.email_to}")
    except Exception as e:
        logger.error(f"Error al enviar email: {str(e)}")
        raise
