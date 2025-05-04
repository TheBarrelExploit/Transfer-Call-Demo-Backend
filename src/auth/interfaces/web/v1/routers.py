from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from src.auth.application.services import AuthService
from .schemas import Token
from .dependencies import get_auth_service
from fastapi.responses import JSONResponse
from src.auth.infrastructure.mfa import MFAService

router = APIRouter(
    prefix="/v1/auth",
    tags=["auth"]
)
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
    username: str,
    code: str,
    secret: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint para verificar y activar MFA"""
    success = await auth_service.verify_mfa(username, secret, code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido"
        )
    return {"message": "MFA habilitado correctamente"}

@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint de login modificado para soportar MFA"""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.mfa_enabled:
        return {
            "mfa_required": True,
            "username": user.username
        }
    
    access_token = await auth_service.create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token/mfa")
async def login_with_mfa(
    username: str,
    code: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Endpoint para completar login con MFA"""
    user = await auth_service.user_repository.get_user_by_username(username)
    if not user or not user.mfa_enabled or not user.mfa_secret:
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