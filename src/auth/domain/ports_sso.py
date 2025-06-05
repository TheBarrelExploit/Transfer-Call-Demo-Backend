# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from abc import ABC, abstractmethod
from typing import Dict, Any


class AuthLoginSSO(ABC):
    @abstractmethod
    def get_auth_url() -> str:
        pass

    @abstractmethod
    async def get_token_from_code(code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_user_info(accss_token: str) -> Dict[str, Any]:
        pass
