from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any
from ..domain.models import PriceBase, PriceHistory


class PricesRepositoryDomain(ABC):
    @abstractmethod
    async def find_by_all_prices(self, page:int, per_page) -> Tuple[List[PriceBase], int]:
        pass

    @abstractmethod
    async def find_by_all_prices_history(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceBase], int]:
        pass

    @abstractmethod
    async def find_by_call_type(self, call_type: str) -> PriceBase:
        pass

    @abstractmethod
    async def create_prices(self, price: str) -> PriceBase:
        pass

    @abstractmethod
    async def consult_history(self, call_type: str) -> List[PriceHistory]:
        pass

    @abstractmethod
    async def update_scheduler(self, data: Dict[str, Any]) -> None:
        pass
