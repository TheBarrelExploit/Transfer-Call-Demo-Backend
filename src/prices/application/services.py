from ..application.interfaces import PricesInterfaces
from ..application.exception import PriceNotFoundException
from ..domain.models import PriceBase, PriceHistory
from ..domain.ports import PricesRepositoryDomain



class PriceService(PricesInterfaces):
    def __init__(self, price: PricesRepositoryDomain):
        self.price = price

    async def get_by_all_price(self):
        price = await self.price.find_by_all_prices()

        if len(price) == 0:
            raise PriceNotFoundException("Prices Not Found")
        
        return price
    
    async def get_by_price(self, class_call:str) -> PriceBase:
        price = await self.price.find_by_call_type(call_type= class_call)
        if not price:
            raise PriceNotFoundException("Price Not Found")

        return price

    async def get_by_history_price(self, class_call:str) -> PriceHistory:
        price = await self.price.consult_history(call_type=class_call)
        if len(price) == 0:
            raise PriceNotFoundException("Price Not Found")
        return price
    
    async def get_by_all_history_price(self):
        price = await self.get_by_all_history_price()
        if len(price ) == 0:
            raise PriceNotFoundException
        return price
              





