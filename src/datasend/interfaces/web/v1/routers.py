from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Security,
    BackgroundTasks,
    UploadFile, 
    File
)
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from src.datasend.infrastructure.email import send_email_background, EmailSchema
from src.datasend.application.services import EmailService, template_email
from src.datasend.interfaces.web.v1.dependencies import get_email_service
from src.users.domain.ports import UserRepository
from src.auth.interfaces.web.v1.dependencies import get_current_user, get_user_repository
from src.auth.infrastructure.security import create_access_token
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/emailsend", tags=["emailsend"])
security = HTTPBearer()

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

class PasswordRecoveryResponse(BaseModel):
    message: str
    success: bool
    token: str 

# ENVIO DE REPORTE VIA EMAIL
@router.post("/send-report-email")
async def send_report_email_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: UserRepository = Depends(get_user_repository),
):
    # Ruta del template (ajustado con Path para mayor portabilidad)
    try:
        # Obtener el token de manera más robusta
        token = credentials.credentials
        if not token or token == "undefined":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización no proporcionado",
            )

        # Obtener usuario actual
        current_user = await get_current_user(token, user_repo)
        logger.info(
            f"Usuario obtenido: {current_user.username}, Email: {current_user.email}"
        )
        
        #Determinar el email de destino
        destination_email = current_user.email_destination or current_user.email
        
        # Verificar que el usuario tenga email destino
        if not destination_email:
            logger.error("El usuario no tiene email registrado ni email alternativo")
            raise HTTPException(
                status_code=400, detail="No se encontró un email válido para enviar el reporte"
            )
        
        
        #validar formato del email de destino si es diferente al principal
        if destination_email != current_user.email:
            try:
                if "@" not in destination_email or "." not in destination_email.split("@")[-1]:
                    raise ValueError("Formato de email invalido")
            except Exception as e:
                logger.error(f"Email de destino invalido{destination_email}")
                raise HTTPException(
                    status_code=400,
                    detail = "El email de destino especificado no tiene un formato valido, por favor actualizar el correo destino a un formato valido."
                )
                
        #renderizar la plantilla usando template_mail
        rendered_body = await template_email(
            template_name = "template_email.html", 
            context={
                "username": current_user.username,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Crear archivo temporal
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            if len(content) > 10 * 1024 * 1024:  # 5MB max
                raise HTTPException(
                    status_code=400,
                    detail="El archivo es demasiado grande (máximo 5MB)",
                )
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Preparar y enviar email
            email_data = EmailSchema(
                email_to=[destination_email],
                subject=f"Reporte de Llamadas - {datetime.now().strftime('%Y-%m-%d')}",
                body=rendered_body,
                attachments=[
                    {
                        "file": temp_file_path,
                        "filename": file.filename or "reporte-llamadas.pdf",
                        "subtype": "pdf",
                    }
                ]
            )
            print(file.filename)

            await send_email_background(background_tasks, email_data)

            return {
                "status": "success",
                "message": f"Reporte enviado a {destination_email}",
                "email": destination_email,
                "is_alternative_email": destination_email != current_user.email
            }
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al enviar reporte: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error interno al procesar la solicitud"
        )

@router.post("/password-recovery")
async def password_recovery(
    background_tasks: BackgroundTasks,
    request: PasswordRecoveryRequest,
    email_service: EmailService = Depends(get_email_service)
):
    """Enviar un correo con instrucciones para recuperar la contraseña"""
    try:
        # Toda la lógica compleja ahora está en el servicio
        success = await email_service.send_password_recovery_email(
            background_tasks=background_tasks,
            email=request.email
        )
        
        # Siempre devolver el mismo mensaje por seguridad
        return {
            "message": "Si el email está registrado, recibirás un correo con instrucciones",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error en password_recovery: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error al procesar la solicitud de recuperación de contraseña"
        )


