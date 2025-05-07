from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from src.users.domain.models import UserBase

class AuthServiceSSO(ABC):

    @abstractmethod
    async def get_login_url(self) -> str:
        pass

    @abstractmethod
    async def process_auth_code(self, code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(self, token:str)->Dict[str, Any]:
        pass

    @abstractmethod
    async def create_user_sso(self, user_info:Dict[str, Any]) -> UserBase:
        pass

    @abstractmethod
    async def create_access_token(self, user:UserBase) -> Dict[str, str]:
        pass

    @abstractmethod
    async def validate_token(self, token: str)-> Optional[UserBase]:
        pass

    
