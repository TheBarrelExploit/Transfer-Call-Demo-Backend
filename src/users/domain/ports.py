from abc import ABC, abstractmethod
from typing import Optional, List
from .models import UserBase


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[UserBase]:
        """Find a user by their ID."""
        pass

    @abstractmethod
    async def find_by_id_microsoft(self, id: str) -> Optional[UserBase]:
        """Find a user by their ID microsoft"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[UserBase]:
        """Find a user by their username"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserBase]:
        """Find a user by their email"""
        pass

    @abstractmethod
    async def create(self, user: UserBase) -> UserBase:
        """Create a new user"""
        pass

    @abstractmethod
    async def update(self, id: str, data: dict) -> UserBase:
        """update a user"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete a user by their ID""" 
        pass

    @abstractmethod
    async def list(self, page: int = 0, per_page: int = 100) -> List[UserBase]:
        pass

    @abstractmethod
    async def change_password(self, email:str, data:dict) -> bool:
        pass

    
    @abstractmethod
    async def image_to_b64(self,img:str) -> str:
        pass