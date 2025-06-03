from fastapi import APIRouter, Depends, HTTPException, status, Security, Query
from dataclasses import asdict
from typing import Optional
from datetime import datetime
from src.tarificador.application.services import CallService
from src.tarificador.application.exception import CallNotFoundException
from src.tarificador.infrastructure.dependencies import (
    get_user_service,
    get_current_payload,
)
from src.tarificador.interfaces.web.v1.schemas import CallResponse, CallBaseResponse, CallRequest, CallGeneralReport, CallGeneralReportResponse, CallGeneralNumberResponse, CallGeneralReportRequest, CallGeneralNumberReport
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
import polars as pl

router = APIRouter(prefix="/v1/calls", tags=["calls"])
security = HTTPBearer()


@router.get("/call_all", response_model=CallResponse, status_code=status.HTTP_200_OK)
async def call_all(
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    try:
        # _ , payload = current_user
        call_data = await call_service.get_all_call()

        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_date_range", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    # _ , payload = current_user
    try:
        if start_date is None or end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start date and end date are required",
            )

        if start_date and not end_date:
            end_date = start_date

        start_date = start_date.replace(" ", "+")
        end_date = end_date.replace(" ", "+")
        call_data = await call_service.get_call_by_date_range(
            start_date=start_date, end_date=end_date
        )
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]
        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_originational",
    response_model=CallResponse,
    status_code=status.HTTP_200_OK,
)
async def call_by_dialed(
    originational_number: str,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    ##_ , payload = current_user
    try:
        call_data = await call_service.get_call_by_dialed_number(originational_number)
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_connected",
    response_model=CallResponse,
    status_code=status.HTTP_200_OK,
)
async def call_by_connected_number(
    connected_number: str,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    # _ , payload = current_user
    try:
        call_data = await call_service.get_call_by_connected_number(
            connected_number=connected_number
        )
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_type_of_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_type_of_call(
    type_of_call: str,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    # _ , payload = current_user
    try:
        call_data = await call_service.get_call_by_type_of_call(
            type_of_call=type_of_call
        )
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_class_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_class_call(
    class_call: str,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    # _ , payload = current_user
    try:
        call_data = await call_service.get_call_by_class_call(class_call=class_call)
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_kind_of_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_kind_of_call(
    kind_of_call: str,
    call_service: CallService = Depends(get_user_service),
    #current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    #credentials: HTTPAuthorizationCredentials = Security(security),
):
    # _ , payload = current_user
    try:
        call_data = await call_service.get_call_by_kind_of_call(
            kind_of_call=kind_of_call
        )
        call_data_validate = [
            CallBaseResponse.model_validate(asdict(call)) for call in call_data
        ]
        print(call_data_validate)

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
@router.post("/call_by", status_code = status.HTTP_200_OK)
async def call_by_filter(
    call_request: CallRequest,
    call_service: CallService = Depends(get_user_service)
):
    call_request_dict = call_request.model_dump(exclude_unset=True)
    if not call_request_dict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontraron datos")
    
    call = await call_service.get_call_by_filter(call_request)
    print(call)

    call_validate = [CallBaseResponse.model_validate(asdict(data)) for data in call]

    return CallResponse(data= call_validate)

@router.get("/general_report",response_model= CallGeneralReportResponse, status_code = status.HTTP_200_OK)
async def general_report(   
    call_service: CallService = Depends(get_user_service),
    entity: str = Query("Entidad",ge="Entidad", description="Nombre de la entidad")
):
    sheet_name = f"general{entity}"
    general_report_data = await call_service.get_report_general(sheet_name=sheet_name)
    general_report_data_validate = [CallGeneralReport.model_validate(report) for report in general_report_data]

    return CallGeneralReportResponse(data = general_report_data_validate)

@router.get("/general_report_all", response_model=CallGeneralReportResponse,status_code=status.HTTP_200_OK)
async def general_report_all(
    call_service: CallService = Depends(get_user_service)
):
    sheet_name = f"adminGeneralReporte"
    general_report_data_all = await call_service.get_report_general(sheet_name=sheet_name, admin =True )
    general_report_data_all_validate = [CallGeneralReport.model_validate(report) for report in general_report_data_all]

    return CallGeneralReportResponse(data = general_report_data_all_validate)

@router.post("/report_number", response_model=CallGeneralNumberResponse ,status_code = status.HTTP_200_OK)
async def general_report_number(
    call_data: CallGeneralReportRequest,
    call_service: CallService = Depends(get_user_service)
):
    if call_data.start_date and call_data.end_time and call_data.start_date > call_data.end_time:
        raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser mayor que la fecha final")
    sheet_name = f"number"

    conditions = []

    if call_data.start_date is not None:
        fecha_inicio_dt = datetime.combine(call_data.start_date, datetime.min.time())
        fecha_inicio_dt = pl.lit(fecha_inicio_dt).cast(pl.Datetime("ms"))
    
    if call_data.end_time is not None:
        fecha_fin_dt = datetime.combine(call_data.end_time, datetime.max.time())
        fecha_fin_dt = pl.lit(fecha_fin_dt).cast(pl.Datetime("ms"))
    
    # Filtro por rango de fechas
# Filtro por rango de fechas (usando solo Fecha inicio según tu ejemplo)
    if call_data.start_date is not None and call_data.end_time is not None:
        conditions.append(
            (pl.col("Fecha inicio") >= fecha_inicio_dt) & 
            (pl.col("Fecha inicio") <= fecha_fin_dt)
        )
    elif call_data.start_date is not None:
        conditions.append(pl.col("Fecha inicio") >= fecha_inicio_dt)
    elif call_data.end_time is not None:
        conditions.append(pl.col("Fecha inicio") <= fecha_fin_dt)
    
    # Otros filtros
    if call_data.originational_number is not None:
        conditions.append(pl.col("Numero") == call_data.originational_number)
    
    if call_data.entity is not None:
        conditions.append(pl.col("Entidad") == call_data.entity)
    
    print(call_data.entity)

    general_report_number = await call_service.get_report_general(sheet_name=sheet_name,admin=False,filter=True,data_filter=conditions)

    general_report_number_validate = [CallGeneralNumberReport.model_validate(general) for general in general_report_number]

    return CallGeneralNumberResponse(data =general_report_number_validate)


    

    
    
