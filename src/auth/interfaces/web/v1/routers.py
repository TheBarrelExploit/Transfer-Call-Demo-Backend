from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.application.services import AuthService
from .schemas import Token
from .dependencies import get_auth_service
from fastapi.responses import JSONResponse
from src.auth.infrastructure.mfa import MFAService
import pyotp
import time
from pydantic import BaseModel
# Añade al inicio de routers.py
from datetime import datetime
# En tu routers.py

import logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"]
)

class MFAVerifyRequest(BaseModel):
    username: str
    code: str
    secret: str

class MFATokenRequest(BaseModel):
    username: str
    code: str

@router.get("/mfa/enable")
async def enable_mfa(
    username: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint mejorado para generación MFA"""
    try:
        logger.info(f"Iniciando generación MFA para {username}")
        
        # 1. Generar secreto
        secret = MFAService.generate_secret()
        logger.info(f"Secreto generado para {username}: {secret}")
        
        # 2. Generar URI
        uri = MFAService.get_totp_uri(username, secret)
        logger.info(f"URI generada para {username}: {uri}")
        
        # 3. Generar QR code
        try:
            qr_code = MFAService.generate_qr_code(uri)
            logger.info(f"QR generado para {username}")
        except Exception as qr_error:
            logger.error(f"Error generando QR: {str(qr_error)}")
            raise HTTPException(
                status_code=500,
                detail="Error generando código QR"
            )
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "uri": uri
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en enable_mfa para {username}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error generando configuración MFA: {str(e)}"
        )

@router.post("/mfa/verify")
async def verify_mfa(
    request_data: MFAVerifyRequest,  # Cambiado de mfa_request a request_data
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint mejorado con sincronización de tiempo"""
    try:
        logger.info(f"Iniciando verificación MFA para {request_data.username}")
        
        # 1. Verificar el código con ventana ampliada
        is_valid = MFAService.verify_code(
            secret=request_data.secret,
            code=request_data.code,
            window=3  # Ventana de 3 códigos (90 segundos)
        )
        
        if not is_valid:
            # Obtener código actual para debug
            current_code = pyotp.TOTP(request_data.secret).now()
            time_remaining = 30 - (int(time.time()) % 30)
            
            logger.warning(
                f"Código inválido. Recibido: {request_data.code}, "
                f"Esperado: {current_code}, "
                f"Tiempo restante: {time_remaining}s"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Código MFA inválido. Código actual: {current_code}"
            )
        
        # 2. Actualizar usuario
        user = await auth_service.user_repository.get_user_by_username(request_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user.mfa_enabled = True
        user.mfa_secret = request_data.secret
        await auth_service.user_repository.update_user(user)
        
        logger.info(f"MFA configurado correctamente para {request_data.username}")
        return {"verified": True}
        
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
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # SIEMPRE requerir MFA
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "mfa_required": True,
            "username": user.username
        }
    )

@router.post("/token/mfa")
async def login_with_mfa(
    request_data: MFATokenRequest,  # Usamos el modelo Pydantic
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
        
        # 3. Verificar código (opcional, ya debería estar verificado)
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
