from datetime import timedelta
from fastapi import BackgroundTasks
from src.auth.infrastructure.security import create_access_token
from src.datasend.infrastructure.email import send_email_background, EmailSchema
from src.users.domain.ports import UserRepository
from jinja2 import Template
from pathlib import Path
from src.shared.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def template_email(template_name: str, context: dict) -> str:
    """Función helper para renderizar templates de email"""
    try:
        template_path = Path() / "src" / "datasend" / "infrastructure" / "template" / template_name
        with open(template_path.resolve(), encoding="utf-8") as f:
            template_str = f.read()
        template = Template(template_str)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error al cargar o renderizar plantilla {template_name}: {str(e)}")
        raise

class EmailService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.base_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:5500/Transfer-Call-Demo/Transfer-Call-Demo-FrontEnd/html')

    async def send_token_email(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        template_name: str,
        subject: str,
        purpose: str,
        expiration_minutes: int = 60,
        extra_context: dict = None,
        provisional_password: str = None,
        silent_fail: bool = False
    ) -> bool:
        """
        Método centralizado para enviar emails con tokens.
        
        Args:
            background_tasks: Objeto BackgroundTasks de FastAPI
            email: Email del destinatario
            template_name: Nombre del template HTML
            subject: Asunto del email
            purpose: Propósito del token ('password_reset', 'welcome', 'complete_profile')
            expiration_minutes: Tiempo de expiración del token
            extra_context: Contexto adicional para el template
            provisional_password: Contraseña provisional (opcional)
            silent_fail: Si True, no lanza excepción si el usuario no existe
        """
        try:
            user = await self.user_repo.find_by_email(email)
            if not user:
                if silent_fail:
                    logger.warning(f"Usuario con email {email} no encontrado")
                    return True  # Retornamos True para no revelar si el email existe
                else:
                    logger.error(f"Usuario con email {email} no encontrado")
                    return False

            # Crear token con propósito específico
            token_data = {
                "id": str(user.id),
                "sub": user.username,
                "email": user.email,
                "purpose": purpose
            }
            
            access_token = create_access_token(
                data=token_data,
                expires_delta=timedelta(minutes=expiration_minutes)
            )
            
            # Contexto base para el template
            context = {
                "username": user.username,
                "action_url": f"{self.base_url}/password.html?token={access_token}",
                "recovery_url": f"{self.base_url}/password.html?token={access_token}",  # Alias para compatibilidad
                "expiration_minutes": expiration_minutes,
                "provisional_password": provisional_password,
                **(extra_context or {})
            }
            
            # Renderizar template
            rendered_body = await template_email(
                template_name=template_name,
                context=context
            )
            
            # Enviar email
            email_data = EmailSchema(
                email_to=[email],
                subject=subject,
                body=rendered_body,
                attachments=[]
            )
            
            await send_email_background(background_tasks, email_data)
            
            logger.info(f"Email de {purpose} enviado a: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar email de {purpose}: {str(e)}", exc_info=True)
            raise

    async def send_welcome_email(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        provisional_password: str
    ) -> bool:
        """
        Método específico para enviar email de bienvenida a nuevos usuarios.
        Utiliza el mismo template que password recovery pero con contexto de bienvenida.
        """
        return await self.send_token_email(
            background_tasks=background_tasks,
            email=email,
            template_name="template_create_user.html",  # Reutiliza el template existente
            subject="Bienvenido - Configura tu contraseña",
            purpose="complete_profile",
            expiration_minutes=1440,  # 24 horas para nuevos usuarios
            extra_context={
                "welcome_message": "¡Bienvenido a nuestra plataforma!",
                "instructions": "Se ha creado tu cuenta. Por favor, configura tu contraseña usando el enlace a continuación.",
                "is_welcome": True  # Flag para el template si necesitas lógica condicional
            },
            provisional_password=provisional_password
        )

    async def send_password_recovery_email(
        self,
        background_tasks: BackgroundTasks,
        email: str
    ) -> bool:
        """
        Método específico para recuperación de contraseña.
        Reutiliza la lógica existente pero con contexto de recuperación.
        """
        return await self.send_token_email(
            background_tasks=background_tasks,
            email=email,
            template_name="template_password_recovery.html",
            subject="Cambio de contraseña",
            purpose="password_reset",
            expiration_minutes=60,  # 1 hora para recuperación
            extra_context={
                "instructions": "Has solicitado cambiar tu contraseña. Usa el enlace a continuación para establecer una nueva contraseña."
            },
            silent_fail=True  # No revelar si el email existe
        )