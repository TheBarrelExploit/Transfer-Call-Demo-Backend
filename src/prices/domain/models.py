from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PriceBase:
    call_type:str
    rate_per_minute:int
    divisa:str
    valid_from: datetime
    valid_to: Optional[datetime]
    is_active: bool
    created_by: str
    created_at: datetime

@dataclass
class PriceHistory:
    action:str
    previous_rate: int
    new_rate: int
    changed_by:str
    changed_at:datetime

