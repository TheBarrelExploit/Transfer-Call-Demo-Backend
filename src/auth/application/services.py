from src.auth.domain.entities import User
from src.auth.infrastructure.security import verify_password, create_access_token
from src.auth.interfaces.repositories import UserRepository  # Import de la interfaz
from datetime import timedelta
from src.shared.config import get_settings
from src.auth.infrastructure.mfa import MFAService #Importa el servicio de MFA

class AuthService:
    def __init__(self, user_repository: UserRepository):  # Usa la interfaz como tipo
        self.user_repository = user_repository

    async def authenticate_user(self, username: str, password: str):
        user = await self.user_repository.get_user_by_username(username)
        #print(f"User found: {user}")
        if not user:
            print(f"Intento de login fallido - usuario no existe: {username}")
            return None
        if not verify_password(password, user.hashed_password):
            print(f"Intento de login fallido - password incorrecto para: {username}")
            return None

        print(f"Login exitoso para: {username}")
        return user
    
    async def enable_mfa(self, username: str) -> dict:
        print(f"Intentando habilitar MFA para: {username}")
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            print("Usuario no encontrado")
            raise ValueError("Usuario no encontrado")
        
        secret = MFAService.generate_secret()
        print(f"Secreto generado: {secret}")
        
        """Habilita MFA para un usuario y devuelve los datos para configurar la app autenticadora"""
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        secret = MFAService.generate_secret()
        uri = MFAService.get_totp_uri(user.username, secret)
        qr_code = MFAService.generate_qr_code(uri)
        
        # Actualiza el usuario (pero no guardes aún el secreto hasta que se verifique)
        return {
            "secret": secret,
            "qr_code": qr_code,
            "uri": uri
        }
    
    async def verify_mfa(self, username: str, secret: str, code: str) -> bool:
        """Verifica un código MFA y activa MFA para el usuario si es correcto"""
        if not MFAService.verify_code(secret, code):
            return False
        
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            return False
            
        user.mfa_enabled = True
        user.mfa_secret = secret
        await self.user_repository.update_user(user)
        return True

    async def create_access_token(self, username: str) -> str:
        access_token_expires = timedelta(minutes=30)
        return create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )