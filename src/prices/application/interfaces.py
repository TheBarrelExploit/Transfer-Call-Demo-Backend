from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any
from ..domain.models import PriceBase, PriceHistory


class PricesInterfaces(ABC):
    @abstractmethod
    async def get_by_all_price(self) -> List[PriceBase]:
        pass

    @abstractmethod
    async def get_by_price(self, class_call: str) -> PriceBase:
        pass

    @abstractmethod
    async def create_price(self, data: Dict[str, Any]) -> PriceBase:
        pass

    @abstractmethod
    async def get_by_all_history_price(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceHistory], int]:
        pass

    @abstractmethod
    async def get_by_history_price(self, class_call: str) -> List[PriceHistory]:
        pass

    @abstractmethod
    async def update_prices(self, data: Dict[str, Any]) -> Dict[str, str]:
        pass
