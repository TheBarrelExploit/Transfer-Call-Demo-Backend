from src.auth.domain.entities import User
from src.auth.infrastructure.security import verify_password, create_access_token
from src.auth.interfaces.repositories import UserRepository  # Import de la interfaz
from datetime import timedelta
from src.shared.config import get_settings

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

    async def create_access_token(self, username: str) -> str:
        access_token_expires = timedelta(minutes=30)
        return create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )