from abc import ABC, abstractmethod
from typing import List
from ..domain.models import CallBase


class CallInterfaces(ABC):
    @abstractmethod
    async def get_all_call(self) -> List[CallBase]:
        pass

    @abstractmethod
    async def get_call_by_dialed_number(self, dialed_number: str) -> List[CallBase]:
        pass

    @abstractmethod
    async def get_call_by_date_range(
        self, start_date: str, end_date: str
    ) -> List[CallBase]:
        pass
