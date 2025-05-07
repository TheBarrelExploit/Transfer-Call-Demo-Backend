from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.application.services import AuthService
from .schemas import Token
from .dependencies import get_auth_service
from fastapi.responses import JSONResponse, RedirectResponse
from src.auth.infrastructure.mfa import MFAService
import pyotp
import time
from pydantic import BaseModel
from src.auth.application.services_sso import AuthServiceSSO
from src.auth.interfaces.web.v1.dependencies import get_auth_service_sso
# Añade al inicio de routers.py
from datetime import datetime
from typing import Optional

import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"]
)

class MFAVerifyRequest(BaseModel):
    username: str
    code: str
    secret: Optional[str] = None  # Hacer el secreto opcional

class MFATokenRequest(BaseModel):
    username: str
    code: str

class MFASetupResponse(BaseModel):
    """Modelo para respuesta de configuración MFA"""
    setup_required: bool
    secret: Optional[str] = None
    qr_code: Optional[str] = None
    uri: Optional[str] = None
    message: str

@router.get("/mfa/status")
async def get_mfa_status(
    username: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Obtiene el estado de configuración MFA del usuario"""
    try:
        user = await auth_service.user_repository.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return {
            "username": username,
            "mfa_enabled": user.mfa_enabled,
            "mfa_configured": user.mfa_enabled and user.mfa_secret is not None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado MFA"
        )

@router.get("/mfa/setup")
async def setup_mfa(
    username: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint para configuración inicial de MFA"""
    try:
        # Verificar si el usuario existe
        user = await auth_service.user_repository.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar si ya tiene MFA configurado
        if user.mfa_enabled and user.mfa_secret:
            # El usuario ya tiene MFA configurado, no necesita configuración adicional
            return MFASetupResponse(
                setup_required=False,
                message="MFA ya está configurado para este usuario"
            )
        
        # Generar nuevo secreto MFA
        secret = MFAService.generate_secret()
        uri = MFAService.get_totp_uri(username, secret)
        qr_code = MFAService.generate_qr_code(uri)
        
        # No guardamos el secreto todavía - esperamos que el usuario lo confirme
        # con un código válido en el endpoint verify
        
        logger.info(f"Configuración MFA inicializada para {username}")
        return MFASetupResponse(
            setup_required=True,
            secret=secret,
            qr_code=qr_code,
            uri=uri,
            message="Escanea el código QR con tu aplicación autenticadora"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en setup MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/mfa/verify")
async def verify_mfa(
    request_data: MFAVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Endpoint unificado para verificación MFA que maneja:
    1. Configuración inicial (cuando se envía el secreto)
    2. Verificación normal (cuando no se envía secreto)
    """
    try:
        logger.info(f"Iniciando verificación MFA para {request_data.username}")
        
        # Obtener usuario
        user = await auth_service.user_repository.get_user_by_username(request_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Determinar si es configuración inicial o verificación normal
        if request_data.secret:
            # Configuración inicial - verificar y guardar el secreto
            if user.mfa_enabled and user.mfa_secret:
                logger.warning(f"Intento de reconfiguración MFA para {request_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El usuario ya tiene MFA configurado"
                )
            
            if not MFAService.verify_code(request_data.secret, request_data.code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Código MFA inválido para configuración inicial"
                )
            
            # Guardar configuración MFA de forma persistente
            user.mfa_enabled = True
            user.mfa_secret = request_data.secret
            await auth_service.user_repository.update_user(user)
            
            logger.info(f"MFA configurado correctamente para {request_data.username}")
            return {
                "verified": True,
                "message": "MFA configurado exitosamente",
                "is_initial_setup": True
            }
        else:
            # Verificación normal - usar secreto almacenado
            if not user.mfa_enabled or not user.mfa_secret:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="MFA no configurado para este usuario"
                )
            
            if not MFAService.verify_code(user.mfa_secret, request_data.code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Código MFA inválido"
                )
            
            logger.info(f"Verificación MFA exitosa para {request_data.username}")
            return {
                "verified": True,
                "message": "Verificación MFA exitosa",
                "is_initial_setup": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en verify_mfa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor: {str(e)}"
        )

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Inicio de sesión estándar, verifica credenciales y determina si se requiere MFA"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Determinar si el usuario necesita configurar MFA o solo verificar
    mfa_status = {
        "mfa_required": True,
        "username": user.username,
    }
    
    # Si el usuario no tiene MFA configurado, indicar que debe configurarlo
    if not user.mfa_enabled or not user.mfa_secret:
        mfa_status["setup_required"] = True
        mfa_status["message"] = "Se requiere configuración MFA"
    else:
        mfa_status["setup_required"] = False
        mfa_status["message"] = "Ingrese el código MFA"
    
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=mfa_status
    )

@router.post("/token/mfa")
async def login_with_mfa(
    request_data: MFATokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Genera token JWT después de verificación MFA exitosa"""
    try:
        logger.info(f"Generando token MFA para {request_data.username}")
        
        # 1. Verificar usuario
        user = await auth_service.user_repository.get_user_by_username(request_data.username)
        if not user:
            logger.error(f"Usuario no encontrado: {request_data.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # 2. Verificar que tenga MFA configurado
        if not user.mfa_enabled or not user.mfa_secret:
            logger.error(f"Usuario sin MFA configurado: {request_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA no configurado para este usuario"
            )
        
        # 3. Verificar código con el secreto almacenado previamente
        if not MFAService.verify_code(user.mfa_secret, request_data.code):
            logger.error(f"Código MFA inválido para {request_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido"
            )
        
        # 4. Generar token
        access_token = await auth_service.create_access_token(user.username)
        
        logger.info(f"Token generado exitosamente para {request_data.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login_with_mfa: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando token de acceso"
        )

@router.post("/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    response = {
        "username": user.username,
        "authenticated": True
    }
    
    if user.mfa_configured:  # Usar el nuevo campo
        response.update({
            "mfa_required": True,
            "setup_required": False,
            "message": "Ingrese el código de verificación"
        })
    else:
        response.update({
            "mfa_required": True,
            "setup_required": True,
            "message": "Configure MFA por primera vez"
        })
    
    return JSONResponse(status_code=202, content=response)


@router.post("/auth/verify-mfa")
async def verify_mfa_login(
    request: MFAVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verifica código MFA (para ambos flujos) y genera token de acceso"""
    # Obtener usuario
    user = await auth_service.user_repository.get_user_by_username(request.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Determinar si es configuración inicial o verificación normal
    if request.secret:
        # Configuración inicial - verificar y guardar el secreto
        if not MFAService.verify_code(request.secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido para configuración inicial"
            )
        
        # Guardar configuración MFA de forma persistente
        user.mfa_enabled = True
        user.mfa_secret = request.secret
        await auth_service.user_repository.update_user(user)
        
        logger.info(f"MFA configurado correctamente para {request.username}")
    else:
        # Verificación normal - usar secreto almacenado
        if not user.mfa_enabled or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MFA no configurado para este usuario"
            )
        
        if not MFAService.verify_code(user.mfa_secret, request.code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido"
            )
    
    # Generar token JWT
    access_token = await auth_service.create_access_token(request.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username
    }

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
            valid_codes.append({
                "offset": i,
                "code": totp.at(valid_time),
                "valid_for": f"{i*30} segundos"
            })
        
        return {
            "current_code": totp.now(),
            "time_remaining": time_remaining,
            "valid_codes": valid_codes,
            "secret_valid": True,
            "timestamp": datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"Error en debug-secret: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/mfa/time-sync-check")
async def time_sync_check(secret: str = Query(...)):
    """Endpoint para verificar sincronización de tiempo"""
    try:
        totp = pyotp.TOTP(secret)
        current_time = time.time()
        time_step = current_time % 30
        
        return {
            "current_time": datetime.fromtimestamp(current_time).isoformat(),
            "time_step_remaining": 30 - time_step,
            "current_code": totp.now(),
            "is_time_synced": True  # Implementar lógica real de verificación
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/mfa/verify-only")
async def verify_mfa_only(
    request: MFATokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.user_repository.get_user_by_username(request.username)
    if not user or not user.mfa_configured:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
    
    if not MFAService.verify_code(user.mfa_secret, request.code):
        raise HTTPException(status_code=401, detail="Código inválido")
    
    return {"verified": True}

@router.get("/login/microsoft")
async def login(
    auth_service:AuthServiceSSO = Depends(get_auth_service_sso) 
):
    login_url = await auth_service.get_login_url()
    return RedirectResponse(url = login_url)


@router.get("/microsoft/callback")
async def auth_callback(
    code:str,
    auth_service:AuthServiceSSO = Depends(get_auth_service_sso)
):
    try:
        auth_result = await auth_service.process_auth_code(code)
        return auth_result
    
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = f"Error durante la autenticación: {str(e)}"
        )
