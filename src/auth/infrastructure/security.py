import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.shared.config import get_settings

settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificación robusta de contraseña"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        # Loggear el error en producción
        return False

def get_password_hash(password: str) -> str:
    """Generación segura de hash"""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=12)  # 12 es un buen balance seguridad/performance
    ).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Tu implementación existente de JWT"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRATION))
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )