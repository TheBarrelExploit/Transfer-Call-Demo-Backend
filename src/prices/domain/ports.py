from abc import ABC, abstractmethod
from ..domain.models import PriceBase

class PricesRepositoryDomain(ABC):

    @abstractmethod
    async def find_by_all_prices(self):
        pass

    @abstractmethod
    async def find_by_id(self, id:str) -> PriceBase:
        pass

    @abstractmethod
    async def find_by_call_type(self,call_type:str) -> PriceBase:
        pass
