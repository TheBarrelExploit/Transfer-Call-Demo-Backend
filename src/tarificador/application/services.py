from typing import List, Dict, Any
from datetime import datetime
from ..domain.models import CallBase
from ..domain.ports import CallRepositoryDomain
from .interfaces import CallInterfaces
from .exception import CallNotFoundException
from ..interfaces.web.v1.schemas import CallRequest


class CallService(CallInterfaces):
    def __init__(self, call_repository: CallRepositoryDomain):
        self.call_repository = call_repository

    async def get_all_call(self) -> List[CallBase]:
        call = await self.call_repository.find_call_all()
        if not call:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_date_range(self, start_date, end_date):
        call = await self.call_repository.find_call_by_date_range(
            start_date=start_date, end_date=end_date
        )

        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_dialed_number(self, dialed_number: int) -> List[CallBase]:
        call = await self.call_repository.find_call_by_dialed_number(
            dialed_number=dialed_number
        )

        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_class_call(self, class_call: str) -> List[CallBase]:
        call = await self.call_repository.find_call_by_class_call(class_call=class_call)
        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_connected_number(
        self, connected_number: str
    ) -> List[CallBase]:
        call = await self.call_repository.find_call_by_connected_number(
            connected_number=connected_number
        )
        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_kind_of_call(self, kind_of_call: str) -> List[CallBase]:
        call = await self.call_repository.find_call_by_kind_of_call(
            kind_of_call=kind_of_call
        )
        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_type_of_call(self, type_of_call: str) -> List[CallBase]:
        call = await self.call_repository.find_call_by_type_of_call(
            type_of_call=type_of_call
        )
        if len(call) == 0:
            raise CallNotFoundException("Not found calls register")
        return call

    async def get_call_by_filter(self, data:CallRequest) -> List[CallBase]:
            query = {}
            # 1. Filtros de fecha (sobre start_date de la BD)
            if data.start_date or data.end_date:
                date_query = {}
                if data.start_date:
                    date_query["$gte"] = data.start_date   # Llamadas que iniciaron después de esta fecha
                if data.end_date:
                    date_query["$lte"] = data.end_date    # Llamadas que iniciaron antes de esta fecha
                query["start_date"] = date_query

            # 2. Campos de coincidencia exacta
            exact_fields = ["originational_number", "connected_number"]
            query.update({
                field: value for field in exact_fields
                if (value := getattr(data, field)) is not None
            })

            # 3. Campos con $in (para listas)
            list_fields = ["type_of_call", "kind_of_call", "class_call"]
            query.update({
                field: {"$in": value} for field in list_fields
                if (value := getattr(data, field))
            })
            
            return await self.call_repository.find_call_by_filter(query)

            