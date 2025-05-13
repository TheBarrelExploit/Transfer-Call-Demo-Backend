from abc import ABC, abstractmethod
from typing import List
from ..domain.models import PriceBase, PriceHistory


class PricesInterfaces(ABC):
     
    @abstractmethod
    async def get_by_all_price(self) -> List[PriceBase]:
        pass

    @abstractmethod
    async def get_by_price(self, class_call:str) -> PriceBase:
        pass

    @abstractmethod
    async def get_by_all_history_price(self) -> List[PriceHistory]:
        pass

    @abstractmethod
    async def get_by_history_price(self, class_call:str) -> List[PriceHistory]:
        pass

    

