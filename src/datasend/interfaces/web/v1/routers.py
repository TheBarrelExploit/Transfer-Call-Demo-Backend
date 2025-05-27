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
from tempfile import NamedTemporaryFile
from datetime import datetime
from jinja2 import Template
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/emailsend", tags=["emailsend"])
security = HTTPBearer()

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

        # Verificar que el usuario tenga email
        if not current_user.email:
            logger.error("El usuario no tiene email registrado")
            raise HTTPException(
                status_code=400, detail="El usuario no tiene un email registrado"
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
                email_to=[current_user.email],
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
                "message": f"Reporte enviado a {current_user.email}",
                "email": current_user.email,
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


# super admin crea usuario y debe proporcionar un correo email, debo enviar mensaje a ese email con 
# una contraseña provisional(sera de 6 digitos random, quedara guardada en base de datos asociado al 
# correo) para inicio de sesion, el usuario debe hacer cambio de contraseña, por lo que debo hacer uso del api que hace que hace cambio
# de contraseña

