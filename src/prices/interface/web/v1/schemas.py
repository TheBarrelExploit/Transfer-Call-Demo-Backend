from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict


class PriceRequest(BaseModel):
    call_type: str
    rate_per_minute: int
    divisa: str
    created_by: str 


class PriceRequestUpdate(BaseModel):
    call_type: str
    rate_per_minute: int
    divisa: str


class PriceUpdate(BaseModel):
    change: List[PriceRequestUpdate]
    update_date: datetime
    user: str


class PriceResponse(BaseModel):
    call_type: str
    rate_per_minute: float
    divisa: str
    valid_from: datetime
    is_active: bool
    created_by: str
    created_at: datetime
    valid_until: Optional[datetime] = None


class PricePaginate(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class PriceHistoryResponse(BaseModel):
    action: str
    call_type: str
    previous_rate: int
    new_rate: int
    changed_by: str
    changed_at: datetime


class PriceResponseList(BaseModel):
    data: List[PriceResponse]
    pagination: PricePaginate


class PriceHistoryList(BaseModel):
    data: List[PriceResponse]
    pagination: PricePaginate
