from abc import ABC, abstractmethod
from typing import List
from ..domain.models import PriceBase,  PriceHistory

class PricesRepositoryDomain(ABC):

    @abstractmethod
    async def find_by_all_prices(self) -> List[PriceBase]:
        pass

    @abstractmethod
    async def find_by_all_prices_history(self) -> List[PriceBase]:
        pass

    @abstractmethod
    async def find_by_call_type(self,call_type:str) -> PriceBase:
        pass
    
    @abstractmethod
    async def create_prices(self, price:str) -> PriceBase:
        pass

    @abstractmethod
    async def consult_history(self, call_type:str) -> List[PriceHistory]:
        pass