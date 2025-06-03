from fastapi import Request, Depends
from polars import DataFrame
from typing import Dict, Annotated
from ..application.services import DashboardApplication
from ..infrastructure.repositories import DashboardRepository

def get_dataframe(request: Request) -> Dict[str,DataFrame]:
    return request.app.state.excel

def get_dashboard(dataframe: Dict[str,DataFrame] = Depends(get_dataframe)) -> DashboardRepository:
    return DashboardRepository(excel=dataframe)

def get_dashboard_services(dataframe:DashboardRepository = Depends(get_dashboard)) -> DashboardApplication:
    return DashboardApplication(service=dataframe)