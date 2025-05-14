from typing import List, Dict, Tuple, Any
from dataclasses import asdict
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.ports import PricesRepositoryDomain
from ..domain.models import PriceBase, PriceHistory
from datetime import datetime, timezone
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

    async def find_by_all_prices(self) -> List[PriceBase]:
        price = await self.collection.find({"is_valid": True})
        data = []
        async for mongo_data in price:
            data.append(PriceBase.from_mongo(mongo_data))
        return data

    async def find_by_all_prices_history(
        self, page: int, per_page: int
    ) -> Tuple[List[PriceHistory], int]:
        skip = (page - 1) * per_page

        price_history = (
            await self.collection_history.find({}).skip(skip=skip).limit(limit=per_page)
        )
        data = []
        async for mongo_data in price_history:
            data.append(PriceHistory.from_mongo(mongo_data))

        total = await self.collection_history.count_documents({})

        return data, total

    async def find_by_call_type(self, call_type: str) -> PriceBase:
        price = await self.collection.find_one(
            {"call_type": call_type, "is_valid": True}
        )
        return PriceBase.from_mongo(price)

    async def create_prices(self, price: PriceBase) -> PriceBase:
        data = asdict(price)

        result = await self.collection.insert_one(data)

        price.id = str(result.inserted_id)

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
            self.execute_price_change,
            "date",
            run_date=price["update_date"],
            args=[job_id],
            id=job_id,
        )
        return {"status": f"Cambio progamado para el dia {price['update_date']}"}

    async def execute_price_change(self, job_id: str):
        bulk_data = self.scheduler.prices_changes.find_one({"_id": job_id})

        async for change in bulk_data["change"]:
            try:
                self.update_single_price(
                    call_type=change["call_type"],
                    new_rate=change["rate_per_minute"],
                    divisa=change["divisa"],
                    user=bulk_data["user"],
                )
            except Exception as e:
                print(f"Error actualizando el {change['call_type']}: {str(e)}")

        self.scheduler.prices_changes.update_one(
            {"_id": job_id}, {"$set": {"status": "completed"}}
        )

    async def update_single_price(
        self, call_type: str, new_rate: int, divisa: str, user: str
    ):
        current_price = await self.collection.find_one({"call_type": call_type})

        await self.collection_history.insert_one(
            {**current_price, "valid_to": datetime.now(timezone.utc)}
        )

        await self.collection.update_one(
            {"call_type": call_type},
            {
                "$set": {
                    "rate_per_minute": new_rate,
                    "divisa": divisa,
                    "valid_from": datetime.now(timezone.utc),
                }
            },
        )
