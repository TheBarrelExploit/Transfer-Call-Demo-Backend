from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    Form,
    Security,
    BackgroundTasks,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi import UploadFile, File
from src.auth.infrastructure.security import oauth2_scheme, invalidate_token
from src.auth.infrastructure.mfa import MFAService
from src.auth.application.services_sso import AuthServiceSSO
from src.auth.application.services import AuthService
from src.auth.interfaces.web.v1.dependencies import get_auth_service_sso
from src.users.domain.models import UserBase, MFAConfig
from src.users.interfaces.web.v1.schemas import UserResponse
from src.users.domain.ports import UserRepository
from src.shared.email import send_email_background, EmailSchema
from .schemas import Token
from .dependencies import (
    get_auth_service,
    get_current_user,
    get_current_user_sso,
    get_mfa_service,
    get_user_repository,
)
from dataclasses import asdict
from pydantic import BaseModel
from datetime import datetime, timezone
from tempfile import NamedTemporaryFile
from typing import Optional, Dict, Any
import logging
import pyotp
import time
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth"])
security = HTTPBearer()

class MFAVerifyResponse(BaseModel):
    verified: bool
    message: str
    is_initial_setup: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    username: Optional[str] = None

class MFAVerifyRequest(BaseModel):
    username: str
    code: str
    secret: Optional[str] = None  # Solo para configuración inicial

class MFATokenRequest(BaseModel):
    username: str
    code: str

class TokenResponse(BaseModel):
    token: str
    token_type: str

class MFASetupResponse(BaseModel):
    """Modelo para respuesta de configuración MFA"""

    setup_required: bool
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    uri: Optional[str] = None
    message: str

@router.get("/mfa/status")
async def get_mfa_status(
    username: str = Query(...), auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.user_repository.find_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "configured": user.mfa is not None and user.mfa.secret is not None,
        "enabled": user.mfa.enabled if user.mfa else False,
        "last_used": user.mfa.last_used_at.isoformat()
        if user.mfa and user.mfa.last_used_at
        else None,
    }

@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    username: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Configuración inicial de MFA"""
    try:
        user = await auth_service.user_repository.find_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Si ya tiene MFA configurado, devolver los datos existentes
        if user.mfa and user.mfa.secret:
            uri = mfa_service.generate_provisioning_uri(username, user.mfa.secret)
            qr_code = mfa_service.generate_qr_code(uri)

            return {
                "setup_required": False,
                "secret": user.mfa.secret,  # Solo para debug
                "qr_code": qr_code,
                "message": "MFA ya está configurado. Escanea el código QR nuevamente si es necesario.",
            }

        # Generar nueva configuración
        secret = mfa_service.generate_secret()
        uri = mfa_service.generate_provisioning_uri(username, secret)
        qr_code = mfa_service.generate_qr_code(uri)

        return {
            "setup_required": True,
            "secret": secret,
            "qr_code": qr_code,
            "message": "Escanea el código QR con tu app autenticadora",
        }

    except Exception as e:
        logger.error(f"Error en configuración MFA: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mfa/enable")
async def enable_mfa(
    username: str = Form(...),
    code: str = Form(...),
    secret: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    """Habilita MFA verificando el código inicial"""
    try:
        logger.info(f"Secret recibido para {username}: {secret[:4]}...{secret[-4:]}")

        # Verificación con ventana ampliada
        if not mfa_service.verify_code(secret, code, window=3):
            current_time = time.time()
            totp = pyotp.TOTP(secret)
            raise HTTPException(
                status_code=401,
                detail={
                    "message": "Código inválido",
                    "expected_codes": {
                        "previous": totp.at(current_time - 30),
                        "current": totp.at(current_time),
                        "next": totp.at(current_time + 30),
                    },
                },
            )
        # Guardar en base de datos
        mfa_config = MFAConfig(
            secret=secret,
            enabled=True,
            backup_codes=[],
            last_used_at=datetime.now(timezone.utc),
        )

        updated = await auth_service.user_repository.update_user_mfa(
            username, mfa_config
        )
        if not updated:
            raise HTTPException(status_code=500, detail="Error al guardar MFA")

        # Verificar guardado
        user = await auth_service.user_repository.find_by_username(username)
        logger.info(
            f"MFA guardado para {username}: {user.mfa.secret[:4]}...{user.mfa.secret[-4:]}"
        )

        return {
            "verified": True,
            "token": await auth_service.create_access_token(user, mfa_verified=True),
            "token_type": "bearer",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en enable_mfa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error crítico en enable_mfa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Error interno del servidor al habilitar MFA"
        )

@router.post("/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa(
    mfa_data:MFAVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verificación estándar de código MFA para login"""
    try:
        mfa_data = mfa_data.model_dump()
        user = await auth_service.user_repository.find_by_username(mfa_data["username"])
        if not user or not user.mfa or not user.mfa.secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA no configurado para este usuario",
            )

        # Verificar código
        if not await auth_service.verify_mfa_login(mfa_data["username"],mfa_data["code"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Código MFA inválido"
            )

        # Actualizar último uso
        await auth_service.user_repository.update_user_mfa(
            username=mfa_data["username"],
            mfa_config=MFAConfig(
                secret=user.mfa.secret,
                enabled=True,
                backup_codes=user.mfa.backup_codes,
                last_used_at=datetime.now(timezone.utc),
            ),
        )

        # Generar token
        token = await auth_service.create_access_token(user, mfa_verified=True)

        return MFAVerifyResponse(
            verified=True,
            message="Verificación MFA exitosa",
            is_initial_setup=False,
            token=token,
            token_type="bearer",
            username=user.username,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en verificación MFA: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en verificación MFA",
        )

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Endpoint principal de login con manejo de MFA"""
    try:
        # 1. Autenticar usuario
        user = await auth_service.authenticate_user(
            form_data.username, form_data.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # 2. Verificar estado MFA
        has_mfa = user.mfa is not None
        mfa_configured = has_mfa and user.mfa.secret is not None
        mfa_enabled = has_mfa and user.mfa.enabled

        # 3. Determinar flujo
        if mfa_configured and mfa_enabled:
            # Usuario con MFA activo - requerir verificación
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "mfa_required": True,
                    "username": user.username,
                    "setup_required": False,
                    "message": "Ingrese su código MFA",
                },
            )
        elif mfa_configured and not mfa_enabled:
            # Usuario con MFA configurado pero no activado
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "mfa_required": True,
                    "username": user.username,
                    "setup_required": True,
                    "message": "Complete la configuración MFA",
                },
            )
        # 4. Usuario sin MFA - token directo
        token = await auth_service.create_access_token(
            user, mfa_verified=not mfa_configured
        )
        return TokenResponse(token=token, token_type="bearer")

    except Exception as e:
        logger.error(f"Error en login: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor",
        )

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    print("print de login: " + form_data.username, form_data.password)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # Generar token de acceso
    token = await auth_service.create_access_token(user)

    # Convertir usuario a UserResponse
    user_dict = asdict(user)
    user_response = UserResponse.model_validate(user_dict)

    # Preparar respuesta
    response_data = {
        "token": token,
        "token_type": "bearer",
        "user": user_response.model_dump(),
    }
    return response_data

# Mantener endpoints de debug para propósitos de desarrollo
@router.get("/mfa/debug-secret")
async def debug_secret(secret: str):
    """Endpoint de debug mejorado"""
    try:
        if not secret or len(secret) < 16:
            raise ValueError("Secreto MFA inválido")
        totp = pyotp.TOTP(secret)
        current_time = time.time()
        time_remaining = 30 - (current_time % 30)
        # Generar códigos válidos
        valid_codes = []
        for i in range(-2, 3):  # -2, -1, 0, 1, 2
            valid_time = current_time + (i * 30)
            valid_codes.append(
                {
                    "offset": i,
                    "code": totp.at(valid_time),
                    "valid_for": f"{i * 30} segundos",
                }
            )
        return {
            "current_code": totp.now(),
            "time_remaining": time_remaining,
            "valid_codes": valid_codes,
            "secret_valid": True,
            "timestamp": datetime.fromtimestamp(current_time).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }
    except Exception as e:
        logger.error(f"Error en debug-secret: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/mfa/time-sync-check")
async def time_sync_check(
    username: str = Query(...),
    secret: str = Query(None),  # Nuevo parámetro opcional
    auth_service: AuthService = Depends(get_auth_service),
    mfa_service: MFAService = Depends(get_mfa_service),
):
    # Endpoint para verificar sincronización de tiempo#
    try:
        # Si se proporciona un secret, usarlo (para configuración inicial)
        # Si no, usar el secret del usuario (para verificación normal)
        if secret:
            current_secret = secret
        else:
            user = await auth_service.user_repository.find_by_username(username)
            if not user or not user.mfa or not user.mfa.secret:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="MFA no configurado para este usuario",
                )
            current_secret = user.mfa.secret
        totp = pyotp.TOTP(current_secret)
        current_time = time.time()
        time_step = current_time % 30

        # Generar códigos válidos en ventana ampliada
        valid_codes = []
        for i in range(-2, 3):  # -2, -1, 0, 1, 2 (ventana más amplia)
            valid_time = current_time + (i * 30)
            valid_codes.append(
                {
                    "offset": i,
                    "code": totp.at(valid_time),
                    "valid_for": f"{i * 30} segundos",
                }
            )
        return {
            "username": username,
            "current_time": datetime.fromtimestamp(current_time).isoformat(),
            "time_step_remaining": 30 - time_step,
            "current_code": totp.now(),
            "valid_codes": valid_codes,
            "time_synced": True,
            "message": "Verifique que el reloj de su dispositivo esté sincronizado",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en verificación de tiempo: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/mfa/toggle")
async def toggle_mfa(
    username: str = Form(...),
    enable: bool = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: UserBase = Depends(get_current_user),  # Seguridad adicional
):
    """Habilita/deshabilita MFA sin regenerar secret"""
    # Verificar que el usuario solo modifique su propio MFA
    if current_user.username != username:
        raise HTTPException(status_code=403, detail="No puede modificar otro usuario")

    user = await auth_service.user_repository.find_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Validar si intenta activar sin tener secret
    if enable and not (user.mfa and user.mfa.secret):
        raise HTTPException(
            status_code=400, detail="Configure MFA primero usando /mfa/setup"
        )

    # Preservar los datos existentes
    mfa_config = MFAConfig(
        secret=user.mfa.secret if user.mfa else None,
        enabled=enable,
        backup_codes=user.mfa.backup_codes if user.mfa else [],
        last_used_at=datetime.now(timezone.utc) if enable else None,
    )
    await auth_service.user_repository.update_user_mfa(username, mfa_config)
    return {
        "enabled": enable,
        "message": f"MFA {'habilitado' if enable else 'deshabilitado'}",
        "requires_verification": enable,  # Frontend puede pedir código si se reactiva
    }

@router.get("/login/microsoft")
async def login(auth_service: AuthServiceSSO = Depends(get_auth_service_sso)):
    login_url = await auth_service.get_login_url()
    return RedirectResponse(url=login_url)

@router.get("/microsoft/callback")
async def auth_callback(
    code: str, auth_service: AuthServiceSSO = Depends(get_auth_service_sso)
):
    try:
        auth_result = await auth_service.process_auth_code(code)
        print(auth_result["token"])
        return RedirectResponse(
            url=f"http://localhost:5500/html/callback.html?token={auth_result['token']}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error durante la autenticación: {str(e)}",
        )

@router.get("/me")
async def info_users_sso(current_user: UserBase = Depends(get_current_user_sso)):
    try:
        user = current_user
        user = asdict(user)
        print(user)
        return UserResponse.model_validate(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"error: {str(e)}"
        )

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: UserBase = Depends(get_current_user),
):
    invalidate_token(token)
    return {"message": "Sesión cerrada exitosamente"}

@router.get("/protected-route")
async def protected_route(user: UserBase = Depends(get_current_user)):
    return {"message": f"Hola {user.username}, estas autenticado!"}


# ENVIO DE REPORTE VIA EMAIL
@router.post("/send-report-email")
async def send_report_email_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Security(security),
    user_repo: UserRepository = Depends(get_user_repository),
):
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

        # Crear archivo temporal
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            if len(content) > 5 * 1024 * 1024:  # 5MB max
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
                body=f"""
                <h2>Reporte de Llamadas</h2>
                <p>Hola {current_user.username},</p>
                <p>Adjunto encontrarás el reporte que solicitaste.</p>
                <p>Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>Saludos,<br>El equipo de soporte</p>
                """,
                attachments=[
                    {
                        "file": temp_file_path,
                        "filename": file.filename or "reporte-llamadas.pdf",
                        "subtype": "pdf",
                    }
                ],
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
