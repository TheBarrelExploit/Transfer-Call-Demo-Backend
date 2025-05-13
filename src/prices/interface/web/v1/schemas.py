from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class PriceRequest(BaseModel):
    call_type: str
    rate_per_minute: int
    divisa:str
    
class PriceResponse(BaseModel):
    call_type:str
    rate_per_minute:int
    divisa:str
    valid_from: datetime
    valid_to: Optional[datetime]
    is_active: bool
    created_by: str
    created_at: datetime

class PriceHistoryResponse(BaseModel):
    action:str
    call_type:str
    previous_rate: int
    new_rate: int
    changed_by:str
    changed_at:datetime

class PriceResponseList(BaseModel):
    data:List[PriceResponse]

class PriceHistoryList(BaseModel):
    data:List[PriceHistoryResponse]



