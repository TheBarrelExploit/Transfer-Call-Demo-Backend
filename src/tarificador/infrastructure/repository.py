from ..domain.ports import CallRepositoryDomain
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.models import CallBase
from typing import List, Dict, Any
from datetime import datetime
from polars import DataFrame



class CallRepository(CallRepositoryDomain):
    def __init__(self, collection: AsyncIOMotorCollection, dataframe:Dict[str, DataFrame]):
        self.collection = collection
        self.dataframe = dataframe

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
        cursor_call_dialed = self.collection.find(
            {"originational_number": dialed_number}
        )
        data = []
        async for mongo_data in cursor_call_dialed:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_class_call(self, class_call: str) -> List[CallBase]:
        cursor_call_class_call = self.collection.find({"class_call": class_call})
        data = []
        async for mongo_data in cursor_call_class_call:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_kind_of_call(self, kind_of_call: str) -> List[CallBase]:
        cursor_call_kind_of_call = self.collection.find({"kind_of_call": kind_of_call})
        data = []
        async for mongo_data in cursor_call_kind_of_call:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_type_of_call(self, type_of_call: str) -> List[CallBase]:
        cursor_call_type_of_call = self.collection.find({"type_of_call": type_of_call})
        data = []
        async for mongo_data in cursor_call_type_of_call:
            data.append(CallBase.from_mongo(mongo_data))
        return data

    async def find_call_by_filter(self, query:Dict[str, Any]) -> List[CallBase]:
        cursor_call_by = self.collection.find(query)
        data_result = []
        async for mongo_data in cursor_call_by:
            data_result.append(CallBase.from_mongo(mongo_data))
        return data_result
    
    async def read_report(self, sheet_name = None, admin = False) ->List[Dict[str, Any]]:
        if admin:  
            return self.dataframe.get(sheet_name).to_dicts()
        
        return self.dataframe.get(sheet_name).to_dicts()
        
