# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from abc import ABC, abstractmethod
from typing import Dict


class DashboardService(ABC):

    @abstractmethod
    async def get_data(self, sheet_name:str, entity:str):
        pass