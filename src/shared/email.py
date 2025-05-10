from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from src.shared.config import get_settings

settings = get_settings()

conf = ConnectionConfig()

async def send_email_with_report():
    message = MessageSchema()

    fm = FastMail(conf)
    await fm.send_message(message)