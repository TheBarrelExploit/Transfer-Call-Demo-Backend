from typing import List, Dict, Tuple, Any
from dataclasses import asdict
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.ports import PricesRepositoryDomain
from ..domain.models import PriceBase, PriceHistory
from src.shared.apscheduler.apscheduler_config import SchedulerConfig
from src.shared.apscheduler.tarea_precios import execute_price_change

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
        price = self.collection.find({}).skip(skip=skip).limit(per_page)
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        
        total = await self.collection.count_documents({})
        return data, total

    async def find_by_all_prices_history(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceHistory], int]:
        skip = (page - 1) * per_page

        price_history = (
            self.collection_history.find({}).skip(skip=skip).limit(limit=per_page)
        )
        data = []
        async for mongo_data in price_history:
            data.append(PriceHistory.from_mongo(mongo_data))

        total = await self.collection_history.count_documents({})

        return data, total

    async def find_by_call_type(self, call_type: str) -> PriceBase:
        price = await self.collection.find_one(
            {"call_type": call_type, "is_active": True}
        )
        return PriceBase.from_mongo(price)

    async def create_prices(self, price: PriceBase) -> PriceBase:
        data = asdict(price)
        data.pop("_id", None)

        result = await self.collection.insert_one(data)

        price._id = str(result.inserted_id)

        return price

    async def consult_history(self, call_type: str) -> List[PriceHistory]:
        history = await self.collection_history.find({"call_type": call_type})
        data = []
        async for mongo_data in history:
            data.append(PriceHistory.from_mongo(mongo_data))
        return data

    async def update_scheduler(self, price: Dict[str, Any]) -> Dict[str, str]:
        job_id = f"bulk_{price['update_date'].strftime('%Y%m%d')}"
        print(job_id)

        self.scheduler.prices_changes.insert_one(
            {"_id": job_id, **price, "status": "pending"}
        )
        self.scheduler.scheduler.add_job(
            "src.shared.apscheduler.tarea_precios:execute_price_change",
            "date",
            run_date=price["update_date"],
            id=job_id,
            kwargs={"job_id": job_id} 
        )
        return {"status": f"Cambio progamado para el dia {price['update_date']}"}
    


