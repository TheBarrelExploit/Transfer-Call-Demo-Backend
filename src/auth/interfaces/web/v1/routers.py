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

@router.get("/mfa/enable")
async def enable_mfa(
    username: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint que siempre genera un nuevo QR/secreto"""
    try:
        # Generar nuevo secreto cada vez
        secret = MFAService.generate_secret()
        uri = MFAService.get_totp_uri(username, secret)
        qr_code = MFAService.generate_qr_code(uri)
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "uri": uri
        }
    except Exception as e:
        logger.error(f"Error generating MFA: {str(e)}")
        raise HTTPException(status_code=400, detail="Error generating MFA setup")

@router.post("/mfa/verify")
async def verify_mfa(
    request: Request,
    mfa_request: MFAVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint de verificación usando MFAService"""
    try:
        logger.info(f"\n{'='*50}\nMFA Verification Request\n"
                   f"Headers: {request.headers}\n"
                   f"Body: {mfa_request}\n"
                   f"{'='*50}")
        
        logger.info(f"Verificando MFA para {mfa_request.username}")
        
        # Verificar el código
        if not MFAService.verify_code(mfa_request.secret, mfa_request.code):
            logger.warning(f"Código MFA inválido para {mfa_request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código MFA inválido"
            )
        
        # Actualizar usuario
        user = await auth_service.user_repository.get_user_by_username(mfa_request.username)
        if not user:
            logger.error(f"Usuario no encontrado: {mfa_request.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user.mfa_enabled = True
        user.mfa_secret = mfa_request.secret
        await auth_service.user_repository.update_user(user)
        
        logger.info(f"MFA activado correctamente para {mfa_request.username}")
        return {"verified": True, "message": "MFA configurado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en verificación MFA: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en el servidor"
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
    username: str,
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Genera token JWT después de verificación MFA exitosa"""
    user = await auth_service.user_repository.get_user_by_username(username)
    if not user or not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación MFA requerida"
        )
    
    if not MFAService.verify_code(user.mfa_secret, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido"
        )
    
    access_token = await auth_service.create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/mfa/debug-secret")
async def debug_secret(secret: str):
    """Endpoint para debug del secreto MFA"""
    try:
        totp = pyotp.TOTP(secret)
        current_time = int(time.time())
        time_remaining = 30 - (current_time % 30)
        
        return {
            "current_code": totp.now(),
            "time_remaining": time_remaining,
            "secret_valid": len(secret) == 32,  # Los secretos TOTP suelen tener 32 caracteres
            "timestamp": current_time
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

