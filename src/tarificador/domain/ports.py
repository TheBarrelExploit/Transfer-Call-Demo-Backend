from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
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

    @abstractmethod
    async def find_call_by_class_call(self, class_call: str) -> CallBase:
        pass

    @abstractmethod
    async def find_call_by_type_of_call(self, type_of_call: str) -> CallBase:
        pass

    @abstractmethod
    async def find_call_by_kind_of_call(self, kind_of_call: str) -> CallBase:
        pass

    @abstractmethod
    async def find_call_by_filter(self, data: Dict[str, Any]) -> List[CallBase]:
        pass

    @abstractmethod
    async def read_report(self,sheet_name: Optional[str]=None, admin: Optional[bool] = False) -> List[Dict]:
        pass