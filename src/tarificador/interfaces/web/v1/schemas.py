# Autores: Denuar Andres Ramos Lezama, Paola Andrea Morales Rodríguez
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from pydantic import BaseModel, Field, AliasPath
from typing import List, Optional
from datetime import datetime, time


class CallRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date:Optional[datetime] = None
    originational_number: Optional[str] = None
    connected_number: Optional[str] = None
    type_of_call: List[str] = None
    kind_of_call: List[str] = None
    class_call: List[str] = None
    dialed_entity:List[str] = None

class CallGeneralReportRequest(BaseModel):
    originational_number:Optional[int] = None
    entity:List[str]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CallGeneralNumberReport(BaseModel):
    dialed_entity:str=Field(validation_alias=AliasPath('Entidad'))
    originational_number:int=Field(validation_alias=AliasPath('Numero'))
    total_call:int=Field(validation_alias=AliasPath('Cant llamadas'))
    any_minutes:time = Field(validation_alias=AliasPath('Cant minutos'))
    total_to_pay:float=Field(validation_alias=AliasPath('Cobro total'))


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
    total_to_pay: float = 0


class CallResponse(BaseModel):
    data: List[CallBaseResponse]
