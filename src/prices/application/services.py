# Autores: Denuar Andres Ramos Lezama
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from ..application.interfaces import PricesInterfaces
from ..application.exception import PriceNotFoundException, PriceNotSchedulerException, PriceNotCreateException
from ..domain.models import PriceBase
from ..domain.ports import PricesRepositoryDomain
from typing import Dict, Any, Tuple, List



class PriceService(PricesInterfaces):
    def __init__(self, price: PricesRepositoryDomain):
        self.price = price

    async def get_by_all_price(self, page:int , per_pages:int) -> Tuple[PriceBase, int]:
        price = await self.price.find_by_all_prices(page=page, per_page=per_pages)

        if len(price) == 0:
            raise PriceNotFoundException("Prices Not Found")

        return price

    async def get_by_price(self, class_call: List) -> Tuple[List[PriceBase], int]:
        price = await self.price.find_by_call_type(call_type=class_call)
        if not price:
            raise PriceNotFoundException("Price Not Found")

        return price

    async def get_by_history_price(self, class_call: List) -> PriceBase:
        price, total = await self.price.consult_history(call_type=class_call)
        if len(price) == 0:
            raise PriceNotFoundException("Price Not Found")
        return price, total

    async def get_by_all_history_price(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceBase], int]:
        price = await self.price.find_by_all_prices_history(page=page, per_page=per_page)
        if len(price) == 0:
            raise PriceNotFoundException
        return price

    async def update_prices(self, data: Dict[str, Any]) -> Dict[str, str]:
        price_response = await self.price.update_scheduler(data)
        if not price_response:
            raise PriceNotSchedulerException("Scheduler no program")
        return price_response
    
    async def create_price(self, data:Dict[str, Any]) -> PriceBase:    
        data = PriceBase(**data)
        prices = await self.price.create_prices(data)

        if not prices:
            raise PriceNotCreateException("Not created")
        
        return prices

        
        
