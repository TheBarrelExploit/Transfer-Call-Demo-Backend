from abc import ABC, abstractmethod
from typing import Dict, List

class DashboardPort(ABC):

    @abstractmethod
    async def get_data_dashboard(self, sheet_name:str, entity:str):
        pass