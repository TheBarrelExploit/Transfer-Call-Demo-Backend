from src.auth.domain.entities import User
from src.auth.infrastructure.security import verify_password, create_access_token
from src.auth.interfaces.repositories import UserRepository
from datetime import timedelta
from src.shared.config import get_settings
from src.auth.infrastructure.mfa import MFAService

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def authenticate_user(self, username: str, password: str):
        user = await self.user_repository.get_user_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def create_access_token(self, username: str) -> str:
        access_token_expires = timedelta(minutes=30)
        return create_access_token(
            data={"sub": username, "mfa_verified": True},  # Añadido claim mfa_verified
            expires_delta=access_token_expires
        )
    
    