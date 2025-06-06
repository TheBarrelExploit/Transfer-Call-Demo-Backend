# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from fastapi import APIRouter, Depends, Query
from src.dashboard.application.services import DashboardApplication
from src.dashboard.infrastructure.dependencies import get_dashboard_services
from ..v1.schemas import ResponseData 

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])

@router.get("/entity_sumary", response_model=ResponseData)
async def entity_sumary(
    entity:str = Query("Entidad", ge="Entidad", description="Nombre de la entidad"),
    service:DashboardApplication = Depends(get_dashboard_services)

): 
    print(entity)
    sheet_name = "dashboard"

    data = await service.get_data(sheet_name=sheet_name, entity =entity)

    return ResponseData.model_validate(data)




