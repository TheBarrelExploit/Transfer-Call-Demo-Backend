from typing import List
from ..domain.models import CallBase
from ..domain.ports import CallRepositoryDomain
from .interfaces import CallInterfaces
from .exception import CallNotFoundException


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

    async def get_call_by_filter(self, data):
        return await super().get_call_by_filter(data)
