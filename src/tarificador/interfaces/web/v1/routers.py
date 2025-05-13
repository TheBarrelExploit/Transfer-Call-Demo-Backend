from fastapi import APIRouter, Depends, HTTPException, status
from dataclasses import asdict
from typing import Optional, Dict,Tuple ,Any
from src.users.domain.models import UserBase
from src.tarificador.application.services import CallService
from src.tarificador.application.exception import CallNotFoundException
from src.tarificador.infrastructure.dependencies import get_user_service, get_current_payload
from src.tarificador.interfaces.web.v1.schemas import CallResponse, CallBaseResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Security

router = APIRouter(prefix="/v1/calls", tags=["calls"])
security = HTTPBearer()

@router.get("/call_all", response_model=CallResponse, status_code=status.HTTP_200_OK)
async def call_all(call_service: CallService = Depends(get_user_service),
                   current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
                   credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        #_ , payload = current_user
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
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    #_ , payload = current_user
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
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
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
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    #_ , payload = current_user
    try:
        call_data = await call_service.get_call_by_connected_number(
            connected_number=connected_number
        )
        call_data_validate = [CallBaseResponse.model_validate(asdict(call)) for call in call_data]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_type_of_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_type_of_call(
    type_of_call: str, call_service: CallService = Depends(get_user_service),
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    #_ , payload = current_user
    try:
        call_data = await call_service.get_call_by_type_of_call(
            type_of_call=type_of_call
        )
        call_data_validate = [CallBaseResponse.model_validate(asdict(call)) for call in call_data]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_class_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_class_call(
    class_call: str, call_service: CallService = Depends(get_user_service),
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    #_ , payload = current_user
    try:
        call_data = await call_service.get_call_by_class_call(class_call=class_call)
        call_data_validate = [CallBaseResponse.model_validate(asdict(call)) for call in call_data]

        return CallResponse(data=call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/call_by_kind_of_call", response_model=CallResponse, status_code=status.HTTP_200_OK
)
async def call_by_kind_of_call(
    kind_of_call: str, call_service: CallService = Depends(get_user_service),
    current_user: Tuple[UserBase, Dict[str, Any]] = Depends(get_current_payload),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    #_ , payload = current_user
    try:
        call_data = await call_service.get_call_by_kind_of_call(
            kind_of_call=kind_of_call
        )
        call_data_validate = [CallBaseResponse.model_validate(asdict(call)) for call in call_data]
        print(call_data_validate)

        return CallResponse(data = call_data_validate)
    except CallNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
