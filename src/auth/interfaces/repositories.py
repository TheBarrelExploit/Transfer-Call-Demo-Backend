from abc import ABC, abstractmethod
from typing import Optional
from src.users.domain.models import UserBase

class UserRepository(ABC):
    """Interfaz abstracta para el repositorio de usuarios"""
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[UserBase]:
        """Obtiene un usuario por su nombre de usuario"""
        pass
    
    @abstractmethod
    async def create_user(self, user: UserBase) -> UserBase:
        """Crea un nuevo usuario"""
        pass