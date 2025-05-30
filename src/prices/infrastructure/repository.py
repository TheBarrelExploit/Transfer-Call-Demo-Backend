from typing import List, Dict, Tuple, Any
from dataclasses import asdict
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.ports import PricesRepositoryDomain
from pytz import timezone
from datetime import datetime, timedelta
from ..domain.models import PriceBase
from src.shared.apscheduler.apscheduler_config import SchedulerConfig

class PriceRepository(PricesRepositoryDomain):
    def __init__(
        self,
        collection: AsyncIOMotorCollection,
        collection_history: AsyncIOMotorCollection,
        scheduler: SchedulerConfig,
    ):
        self.collection = collection
        self.collection_history = collection_history
        self.scheduler = scheduler

    async def find_by_all_prices(self, page:int, per_page:int) -> Tuple[List[PriceBase], int]:
        skip = (page - 1) * per_page
        price = self.collection.aggregate(
            [
                {
                    "$set": {  # Solo afecta los resultados, NO la BD
                        "rate_per_minute": {"$divide": ["$rate_per_minute", 100]},
                    }
                },
                { "$limit": per_page },
                { "$skip": skip }
            ]
        )
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        
        total = await self.collection.count_documents({})
        return data, total

    async def find_by_all_prices_history(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceBase], int]:
        skip = (page - 1) * per_page

        price_history = (
            self.collection_history.find({"$expr":{"gt": [
                {"$divide":["$rate_per_minute",100]}
            ]}}).skip(skip=skip).limit(limit=per_page)
        )
        data = []
        async for mongo_data in price_history:
            data.append(PriceBase.from_mongo(mongo_data))

        total = await self.collection_history.count_documents({})

        return data, total

    async def find_by_call_type(self, call_type: str) -> PriceBase:
        price = self.collection.aggregate(
            [
                {
                    "$match": {
                        "call_type": {"$in": call_type},
                        "is_active": True
                    }
                },
                {
                    "$set": {  # Solo afecta los resultados, NO la BD
                        "rate_per_minute": {"$divide": ["$rate_per_minute", 100]},
                    }
                }
            ]
        )
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        total = await self.collection_history.count_documents({"call_type":{"$in": call_type}, "is_active": True})
        return data, total

    async def create_prices(self, price: PriceBase) -> PriceBase:
        data = asdict(price)
        data.pop("_id", None)

        result = await self.collection.insert_one(data)

        price._id = str(result.inserted_id)

        return price

    async def consult_history(self, call_type:List) -> Tuple[List[PriceBase],int]:
        price = self.collection_history.aggregate(
            [
                {
                    "$match": {
                        "call_type": {"$in": call_type},
                    }
                },
                {
                    "$set": {  # Solo afecta los resultados, NO la BD
                        "rate_per_minute": {"$divide": ["$rate_per_minute", 100]},
                    }
                }
            ]
        )
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        total = await self.collection_history.count_documents({"call_type": {"$in": call_type}})
        return data, total

    async def update_scheduler(self, price: Dict[str, Any]) -> Dict[str, str]:
        job_id = f"bulk_{price['update_date'].strftime('%Y%m%d%H:%M:%S')}"
        print(job_id)

        self.scheduler.prices_changes.insert_one(
            {"_id": job_id, **price, "status": "pending"}
        )

        bogota_tz = timezone('America/Bogota')
        test_date = datetime.now(bogota_tz) + timedelta(minutes=1)

        self.scheduler.scheduler.add_job(
            "src.shared.apscheduler.tarea_precios:execute_price_change",
            "date",
            run_date=test_date,
            id=job_id,
            kwargs={"job_id": job_id} 
        )
        return {"status": f"Cambio progamado para el dia {price['update_date']}"}
    


