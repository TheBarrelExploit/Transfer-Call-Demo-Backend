from abc import ABC, abstractmethod
from typing import List
from .models import CallBase


class CallRepositoryDomain(ABC):
    @abstractmethod
    async def find_call_all(self) -> List[CallBase]:
        pass

    @abstractmethod
    async def find_call_by_dialed_number(self, dialed_number: str) -> CallBase:
        pass

    @abstractmethod
    async def find_call_by_connected_number(self, connected_number: str) -> CallBase:
        pass

    @abstractmethod
    async def find_call_by_date_range(self, start_date: str, end_date: str) -> CallBase:
        pass
