from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CallRequest(BaseModel):
    start_date: datetime = None
    end_date:datetime = None
    originational_number: str = None
    connected_number: str = None
    type_of_call: List[str] = None
    kind_of_call: List[str] = None
    class_call: List[str] = None

class CallBaseResponse(BaseModel):
    id: str = Field(alias="_id")
    originational_number: str
    connected_number: str
    start_date: datetime
    end_date: datetime
    time_spent_in_call: str = "00:00:00"
    type_of_call: str
    kind_of_call: str
    class_call: str
    any_minutes: int = 0
    total_to_pay: int = 0


class CallResponse(BaseModel):
    data: List[CallBaseResponse]
