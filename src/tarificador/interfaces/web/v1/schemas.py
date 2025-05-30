from pydantic import BaseModel, Field, AliasPath
from typing import List, Optional
from datetime import datetime


class CallRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date:Optional[datetime] = None
    originational_number: Optional[str] = None
    connected_number: Optional[str] = None
    type_of_call: List[str] = None
    kind_of_call: List[str] = None
    class_call: List[str] = None

class CallGeneralReportRequest(BaseModel):
    originational_number:str
    entity:str
    start_date: Optional[datetime] = None
    end_time: Optional[datetime] = None

class CallGeneralNumberReport(BaseModel):
    entity:str=Field(validation_alias=AliasPath('Entidad'))
    originational_number:str=Field(validation_alias=AliasPath('Numero'))
    total_call:str=Field(validation_alias=AliasPath('Numero'))
    any_minute:str = Field(validation_alias=AliasPath('Cobro total'))
    total_to_pay:str=Field(validation_alias=AliasPath('Numero'))


class CallGeneralNumberResponse(BaseModel):
    data:List[CallGeneralNumberReport]

class CallGeneralReport(BaseModel):
    dialed_entity:str=Field(validation_alias=AliasPath('Entidad'))
    local:int =Field(validation_alias=AliasPath('Local'))
    premium:int = Field(validation_alias=AliasPath('premium'))
    international:int = Field(validation_alias=AliasPath('international'))
    lda:int = Field(validation_alias=AliasPath('larga distancia intra'))
    ldi:int = Field(validation_alias=AliasPath('larga distancia inter'))
    call_total:int = Field(validation_alias=AliasPath("total llamadas"))
    any_minutes:int = Field(validation_alias=AliasPath('minutos a cobrar'))
    total_to_pay:float = Field(validation_alias=AliasPath('cobro total'))

class CallGeneralReportResponse(BaseModel):
    data:List[CallGeneralReport]


class CallBaseResponse(BaseModel):
    id: str = Field(alias="_id")
    originational_number: str
    dialed_entity:str
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
