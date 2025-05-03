from src.auth.domain.entities import User
from src.auth.infrastructure.security import verify_password, create_access_token
from src.auth.interfaces.repositories import UserRepository  # Import de la interfaz
from datetime import timedelta
from src.shared.config import get_settings

class AuthService:
    def __init__(self, user_repository: UserRepository):  # Usa la interfaz como tipo
        self.user_repository = user_repository

    async def authenticate_user(self, username: str, password: str) -> User | None:
        user = await self.user_repository.get_user_by_username(username)
        print(f"User found: {user}")
        if not user:
            print("User not found")
            return None
        from src.auth.infrastructure.security import verify_password
        print(f"Comparing passwords: {password} vs {user.hashed_password}")  # Debug
        print(f"Verify result: {verify_password(password, user.hashed_password)}")  # Debug
        
        if not verify_password(password, user.hashed_password):
            print("Password verification failed")  # Debug
            return None
   
        return user

    async def create_access_token(self, username: str) -> str:
        access_token_expires = timedelta(minutes=30)
        return create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )