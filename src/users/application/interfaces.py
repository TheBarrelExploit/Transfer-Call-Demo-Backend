from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..domain.models import UserBase


class UserServiceUser(ABC):
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def get_by_microsoft_id(self, id: str) -> Optional[UserBase]:
        pass

    @abstractmethod
    async def create_user(self, user: UserBase) -> UserBase:
        pass

    @abstractmethod
    async def create_user_sso(self, user: UserBase) -> UserBase:
        pass

    @abstractmethod
    async def update_user(self, id: str, data: Dict[str, Any]) -> UserBase:
        pass

    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 10) -> List[UserBase]:
        pass
    