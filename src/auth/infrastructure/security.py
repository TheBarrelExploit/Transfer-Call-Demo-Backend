import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from src.shared.config import get_settings
import time
import pyotp
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request

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
    """Tu implementación existente de JWT"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_code(secret: str, code: str) -> bool:
    """Verificación robusta con ventana de tiempo ampliada"""
    totp = pyotp.TOTP(secret)

    # Verifica el código actual y los 2 códigos anteriores/siguientes (ventana de 2)
    return totp.verify(code, valid_window=2)


def verify_token(token: str):
    """Verifica y decodifica un token JWT"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def invalidate_token(token: str):
    blacklisted_tokens.add(token)


def is_token_blacklisted(token: str) -> bool:
    return token in blacklisted_tokens
