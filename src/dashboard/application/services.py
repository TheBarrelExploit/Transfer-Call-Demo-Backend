from ..application.interfaces import DashboardService
from ..infrastructure.repositories import DashboardRepository
from typing import Dict


class DashboardApplication(DashboardService):
    def __init__(self,service:DashboardRepository):
        self.service = service

    async def get_data(self, sheet_name, entity):
        data = await self.service.get_data_dashboard(sheet_name=sheet_name, entity=entity) 
        return data
