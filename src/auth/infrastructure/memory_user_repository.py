from src.auth.domain.entities import User
from src.auth.interfaces.repositories import UserRepository
from typing import Optional
from src.auth.infrastructure.security import get_password_hash

class MemoryUserRepository(UserRepository):
    """Implementación en memoria para pruebas"""
    
    def __init__(self):
        self.users = {
            "testuser": User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                disabled=False,
                full_name="Test User"
            )
        }

    async def get_user_by_username(self, username: str) -> Optional[User]:
        return self.users.get(username)

    async def create_user(self, user: User) -> User:
        self.users[user.username] = user
        return user