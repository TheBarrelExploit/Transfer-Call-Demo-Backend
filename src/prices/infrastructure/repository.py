from typing import List
from dataclasses import asdict  
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.ports import PricesRepositoryDomain
from ..domain.models import PriceBase, PriceHistory


class PriceRepository(PricesRepositoryDomain):
    def __init__(self, collection:AsyncIOMotorCollection,collection_history:AsyncIOMotorCollection):
        self.collection = collection
        self.collection_history = collection_history

    async def find_by_all_prices(self) -> List[PriceBase]:
        price = await self.collection.find({"is_valid":True})
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        return data
    
    async def find_by_all_prices_history(self) -> List[PriceHistory]:
        price_history = await self.collection_history.find({})
        data = []
        async for mongo_data in price_history:
            data.append(PriceHistory.from_mongo(mongo_data))
        return data
         
    async def find_by_call_type(self, call_type:str) -> PriceBase:
        price = await self.collection.find_one({"call_type": call_type, "is_valid":True})
        return PriceBase.from_mongo(price)

    async def create_prices(self, price:PriceBase) -> PriceBase:
        data = asdict(price)

        result = await self.collection.insert_one(data)

        price.id = str(result.inserted_id)

        return price
    
    async def consult_history(self, call_type:str) -> List[PriceHistory]:
        history = await self.collection_history.find({"call_type": call_type})
        data = []
        async for mongo_data in history:
            data.append(PriceHistory.from_mongo(mongo_data))
        return data

        
    
    
        
 

        
        

