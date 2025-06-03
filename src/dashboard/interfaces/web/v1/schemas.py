from pydantic import BaseModel, Field, AliasPath


class ResponseData(BaseModel):
    total_call:int=Field(validation_alias=AliasPath('Total'))
    total_answered:int=Field(validation_alias=AliasPath('Respondidas'))
    total_answered_direct:int=Field(validation_alias=AliasPath('Respondidas directas'))
    total_answered_transferred:int=Field(validation_alias=AliasPath('Respondidas transferidas'))
    total_transferred:int=Field(validation_alias=AliasPath('Transferidas'))
    total_transferred_response:int=Field(validation_alias=AliasPath('Transferidas Respondidas'))
    total_missed_transferred:int=Field(validation_alias=AliasPath('Transferidas perdidas'))
    total_missed:int=Field(validation_alias=AliasPath('No respondidas'))
    total_returned_missed:int=Field(validation_alias=AliasPath('No respondidas devueltas'))
    total_not_returned_missed:int=Field(validation_alias=AliasPath('No respondidas no devueltas'))
    total_not_returned: int=Field(validation_alias=AliasPath('Llamadas no devueltas'))
    total_not_returned_waiting: int=Field(validation_alias=AliasPath('Llamadas no devueltas en espera'))
    total_not_returned_no_cli: int=Field(validation_alias=AliasPath('Llamadas no devueltas CLI'))
    total_calls_returned:int=Field(validation_alias=AliasPath('Llamadas devueltas'))
    total_calls_agent:int=Field(validation_alias=AliasPath('Llamadas devueltas agente'))
    total_calls_client:int=Field(validation_alias=AliasPath('Llamadas devueltas cliente'))
    total_restant_calls:int =Field(validation_alias=AliasPath('Tiempo restante'))