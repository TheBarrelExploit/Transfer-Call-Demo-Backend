from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from src.shared.config import get_settings
from typing import Optional
import bcrypt
import time
import pyotp
import logging

logger = logging.getLogger(__name__)

settings = get_settings()
blacklisted_tokens = set()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificación robusta de contraseña"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception as e:
        # Loggear el error en producción
        return False


def get_password_hash(password: str) -> str:
    """Generación segura de hash"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12),  # 12 es un buen balance seguridad/performance
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Crea un token JWT con el nuevo formato que incluye:
    - id: ID del usuario (requerido)
    - sub: username (mantenido por compatibilidad)
    - email: email del usuario
    - roles: roles del usuario
    - mfa_verified: estado de verificación MFA
    - auth_provider: proveedor de autenticación
    """
    to_encode = data.copy()
    if "id" not in to_encode:
        raise ValueError("El payload del token debe incluir el 'id' del usuario")
    
    if "sub" not in to_encode:
        to_encode["sub"] = to_encode.get("username", "")
        
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION)
    )
    to_encode.update({"exp": expire})
    
    try: 
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    except Exception as e:
        logger.error(f"Error creating acces token:  {str(e)}" )
        raise

def verify_code(secret: str, code: str) -> bool:
    """Verificación robusta con ventana de tiempo ampliada"""
    totp = pyotp.TOTP(secret)

    # Verifica el código actual y los 2 códigos anteriores/siguientes (ventana de 2)
    return totp.verify(code, valid_window=2)


def verify_token(token: str):
    """
    Verifica y decodifica un token JWT.
    Devuelve el payload si es válido, None si no lo es.
    """
    try:
        if is_token_blacklisted(token):
            logger.warning("this token is blacklisted")
            return None
        
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        #validacion adicional para el payload, por si no esta ni id ni username
        if "id" not in payload and "sub "not in payload:
            logger.warning("oken no contiene identificador de usuario")
            return None
        
        return payload
    except JWTError as e:
        logger.warning(f"Token inválido: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al verificar token: {str(e)}")
        return None


def invalidate_token(token: str) -> None:
    #Añade un token a la lista negra
    try:
        if token not in blacklisted_tokens:
            blacklisted_tokens.add(token)
            logger.info(f"Token invalidado: {token[:10]}...")
    except Exception as e:
        logger.error(f"Error al invalidar token: {str(e)}")


def is_token_blacklisted(token: str) -> bool:
    #Verifica si un token está en la lista negra
    return token in blacklisted_tokens


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Función auxiliar para extraer específicamente el ID de usuario del token.
    Prioriza el campo 'id', pero mantiene compatibilidad con 'sub' si no existe.
    """
    payload = verify_token(token)
    if not payload:
        return None
        
    return payload.get('id') or payload.get('sub')