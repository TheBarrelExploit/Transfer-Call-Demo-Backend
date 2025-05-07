from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthLoginSSO(ABC):
    
    @abstractmethod
    def get_auth_url()->str:
        pass

    @abstractmethod
    async def get_token_from_code(code:str)->Dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(accss_token:str) -> Dict[str, Any]:
        pass

