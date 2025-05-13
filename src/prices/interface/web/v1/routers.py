from fastapi import APIRouter, Depends, HTTPException, status
from dataclasses import asdict
from typing import Optional, Dict,Tuple ,Any
from ..v1.schemas import PriceResponseList, PriceRequest, PriceHistoryList, PriceResponse, PriceHistoryResponse
from src.prices.infrastructure.dependencies import get_service_price
from src.prices.application.exception import PriceNotFoundException
from src.prices.application.services import PriceService
from src.prices.domain.models import PriceBase, PriceHistory


router = APIRouter(prefix="/v1/prices", tags=["calls"])

@router.get("/prices_all", response_model= PriceResponseList, status_code=status.HTTP_200_OK)
async def prices_all(
    prices_services: PriceService = Depends(get_service_price)
)-> PriceResponseList:
    prices_all = await prices_services.get_by_all_price()
    prices_all_validate = [ PriceResponse.model_validate(asdict(prices)) for prices in prices_all]

    return PriceResponseList(data= prices_all_validate)

@router.get("/prices_by", response_model=PriceResponseList,status_code=status.HTTP_200_OK)
async def price_by(
    class_price: str,
    prices_services: PriceService = Depends(get_service_price)   
) ->PriceResponseList:
    prices_by = await prices_services.get_by_price(class_call= class_price)
    prices_by_validate = [ PriceResponse.model_validate(asdict(prices)) for prices in prices_by]

    return PriceResponseList(data = prices_by_validate)

@router.get("/prices_history_all", response_model=PriceHistoryList, status_code= status.HTTP_200_OK)
async def history_all(
    prices_services: PriceService = Depends(get_service_price)
) -> PriceHistoryList:
    prices_history_all = await prices_services.get_by_all_history_price()
    prices_history_all_validate = [ PriceHistoryResponse.model_validate(asdict(prices)) for prices in prices_history_all]
    return PriceHistoryList(data = prices_history_all_validate)

