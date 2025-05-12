from abc import ABC, abstractmethod
from ..domain.models import PriceBase


class PricesInterfaces(ABC):
     
    @abstractmethod
    async def get_by_all_price(self):
        pass

    @abstractmethod
    async def get_by_price(self, class_call:str) -> PriceBase:
        pass

