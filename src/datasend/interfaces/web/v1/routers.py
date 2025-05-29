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
from src.users.domain.ports import UserRepository
from src.auth.interfaces.web.v1.dependencies import get_current_user, get_user_repository
from src.auth.infrastructure.security import create_access_token
from tempfile import NamedTemporaryFile
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jinja2 import Template
from pathlib import Path

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

async def template_email(template_name: str, context:dict)->str:
    try:
        template_path = Path()/ "src" / "datasend" / "infrastructure" / "template" / template_name
        with open(template_path.resolve(), encoding="utf-8") as f:
            template_str = f.read()
        template = Template(template_str)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error al cargar o renderizar plantilla {template_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la plantilla de email: {str(e)}"
        )

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


@router.post("/password-recovery", )
async def password_recovery(
    background_tasks: BackgroundTasks,
    request: PasswordRecoveryRequest,
    user_repo: UserRepository = Depends(get_user_repository)
):
    #Enviar un correo con instrucciones para recuperar la contraseña
    try:
        #existe el email en la base de datos?
        user = await user_repo.find_by_email(request.email)
        if not user:
            logger.warning(f"Intento de recuperacion para email no registrado:{request.email}")
            return {
                "message": "Si el email esta registrado, recibira un correo con instrucciones",
                "succes": True
            }
        
        token_data = {
            "id": str(user.id),
            "sub":user.username,
            "email": user.email,
            "purpose": "password_reset"
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=60)
        )
        
        #preparar el enlace de recuperacion
        recovery_url = f"http://127.0.0.1:5500/Transfer-Call-Demo/Transfer-Call-Demo-FrontEnd/html/password.html?token={access_token}"

        #renderizar el template del email
        rendered_body = await template_email(
            template_name= "template_password_recovery.html",
            context = {
                "username": user.username,
                "recovery_url": recovery_url,
            }
        )
        
        #preparar y enviar el email
        email_data = EmailSchema(
            email_to=[request.email],
            subject="Cambio de contraseña",
            body= rendered_body,
            attachments= []
        )
        
        await send_email_background(background_tasks, email_data)
        
        logger.info(f"Email de cambio de contraseña enviado a: {request.email}")
        
        return{
            "message": "Si el email esta registrado, recibiras un correo con instrucciones",
            "success": True
        }
    except Exception as e:
        logger.error(f"Error en password_recovery: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error al procesar la solicitud de recuperacion de contraseña"
        )