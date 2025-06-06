# Autores: Denuar Andres Ramos Lezama
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from fastapi import APIRouter, Depends, HTTPException, status, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dataclasses import asdict
from typing import Optional, Dict, Tuple, Any
from ..v1.schemas import (
    PriceResponseList,
    PriceRequest,
    PriceHistoryList,
    PriceResponse,
    PriceHistoryResponse,
    PriceUpdate,
)
from src.prices.infrastructure.dependencies import get_service_price
from src.prices.application.exception import PriceNotFoundException
from src.prices.application.services import PriceService


router = APIRouter(prefix="/v1/prices", tags=["prices"])
security = HTTPBearer()

@router.get(
    "/prices_all", response_model=PriceResponseList, status_code=status.HTTP_200_OK
)
async def prices_all(
    page: int = Query(1, ge=1, description="Numero de página"),
    per_page: int = Query(10, le=100, description="Items por página"),
    prices_services: PriceService = Depends(get_service_price),
    #credentials: HTTPAuthorizationCredentials = Security(security)
) -> PriceResponseList:
    prices_all, total = await prices_services.get_by_all_price(page=page, per_pages=per_page)
    prices_all_validate = [
        PriceResponse.model_validate(asdict(prices)) for prices in prices_all
    ]

    total_pages = (total + per_page - 1) // per_page
    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }

    return PriceResponseList(data=prices_all_validate, pagination= pagination)


@router.get(
    "/prices_by", response_model=PriceResponseList, status_code=status.HTTP_200_OK
)
async def price_by(
    class_price: str,
    page: int = Query(1, ge=1, description="Numero de página"),
    per_page: int = Query(10, le=100, description="Items por página"),
    prices_services: PriceService = Depends(get_service_price)
) -> PriceResponseList:
    class_prices= [item.strip() for item in class_price.split(',')]
    prices_by, total  = await prices_services.get_by_price(class_call=class_prices)
    prices_by_validation = [PriceResponse.model_validate(asdict(prices)) for prices in prices_by]
    
    total_pages = (total + per_page - 1) // per_page
    
    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }

    return PriceResponseList(data=prices_by_validation, pagination= pagination)


@router.get(
    "/prices_history_all",
    response_model=PriceHistoryList,
    status_code=status.HTTP_200_OK,
)
async def history_all(
    page: int = Query(1, ge=1, description="Numero de página"),
    per_page: int = Query(10, le=100, description="Items por página"),
    prices_services: PriceService = Depends(get_service_price),
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> PriceHistoryList:
    prices_history_all, total = await prices_services.get_by_all_history_price(
        page=page, per_page=per_page
    )
    prices_history_all_validate = [
        PriceResponse.model_validate(asdict(prices))
        for prices in prices_history_all
    ]

    total_pages = (total + per_page - 1) // per_page
    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }

    return PriceHistoryList(data=prices_history_all_validate, pagination=pagination)


@router.get(
    "/prices_history_by",
    response_model=PriceHistoryList,
    status_code=status.HTTP_200_OK,
)
async def history_by(
    class_price: str, 
    prices_service: PriceService = Depends(get_service_price),
    page: int = Query(1, ge=1, description="Numero de página"),
    per_page: int = Query(10, le=100, description="Items por página"),
    #credentials: HTTPAuthorizationCredentials = Security(security)
) -> PriceHistoryList:
    class_prices = [item.strip() for item in class_price.split(',')]
    price_history_by, total = await prices_service.get_by_history_price(class_call=class_prices)
    total_pages = (total + per_page - 1) // per_page
    price_history_by_validate = [PriceResponse.model_validate(asdict(price)) for price in price_history_by]
    pagination = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }
    return PriceHistoryList(data=price_history_by_validate, pagination= pagination)


@router.put("/price_update", status_code=status.HTTP_202_ACCEPTED)
async def price_update(
    price_data: PriceUpdate,
    prices_service: PriceService = Depends(get_service_price),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    price_data_validate = price_data.model_dump()

    if not price_data_validate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No se encontro información"
        )

    price_response = await prices_service.update_prices(price_data_validate)

    return price_response

@router.post("/price_create", response_model=PriceResponse, status_code=status.HTTP_200_OK)
async def create_price(
   price_data: PriceRequest,
   price_service: PriceService = Depends(get_service_price),
   credentials: HTTPAuthorizationCredentials = Security(security)
):
    price_data_validate = price_data.model_dump()

    if not price_data_validate:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, detail = "No se encontro información"
        )
    price_response = await price_service.create_price(price_data_validate)

    return PriceResponse.model_validate(asdict(price_response))
