from ..domain.ports import CallRepositoryDomain
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.models import CallBase
from typing import Optional, List
from datetime import datetime


class CallRepository(CallRepositoryDomain):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def find_call_all(self) -> List[CallBase]:
        cursor_call_data = self.collection.find({})
        data = []
        async for mongo_data in cursor_call_data:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_connected_number(self, connected_number):
        cursor_call_number = self.collection.find(
            {"connected_number": connected_number}
        )
        data = []
        async for mongo_data in cursor_call_number:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_date_range(self, start_date, end_date):
        cursor_call_date = self.collection.find(
            {
                "start_date": {"$lte": datetime.fromisoformat(end_date)},
                "end_date": {"$gte": datetime.fromisoformat(start_date)},
            }
        )
        data = []
        async for mongo_data in cursor_call_date:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_dialed_number(self, dialed_number: str) -> List[CallBase]:
        cursor_call_dialed = self.collection.find({"originational_number": dialed_number})
        data = []
        async for mongo_data in cursor_call_dialed:
            data.append(CallBase.from_mongo(mongo_data))
        return data
