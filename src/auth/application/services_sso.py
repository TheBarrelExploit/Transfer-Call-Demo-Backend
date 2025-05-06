from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

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

    
