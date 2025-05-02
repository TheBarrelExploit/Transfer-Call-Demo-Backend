from abc import ABC, abstractmethod
from typing import Optional
from src.auth.domain.entities import User

class UserRepository(ABC):
    """Interfaz abstracta para el repositorio de usuarios"""
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario"""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Crea un nuevo usuario"""
        pass