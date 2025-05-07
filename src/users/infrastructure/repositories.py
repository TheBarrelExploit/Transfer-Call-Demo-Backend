from dataclasses import asdict
from bson import ObjectId
from typing import Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.models import UserBase
from ..domain.ports import UserRepository


class DBUserRepository(UserRepository):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def find_by_id(self, id: str) -> UserBase | None:
        user_data = await self.collection.find_one({"_id": ObjectId(id)})
        return UserBase.from_mongo(user_data) if user_data else None
    
    async def find_by_id_microsoft(self, id:str):
        user_data = await self.collection.find_one({"microsoft_id_account": id})
        return UserBase.from_mongo(user_data) if user_data else None
        
    async def find_by_email(self, email:str) -> UserBase | None:
        user_data = await self.collection.find_one({"email": email})
        return UserBase.from_mongo(user_data) if user_data else None
    
    async def create(self, user:UserBase) -> UserBase | None:
        data = asdict(user)
        data.pop("_id", None)
        result = await self.collection.insert_one(data)
        user._id = str(result.inserted_id)
        return user
   
    async def update(self, id:str, data:dict) -> Optional[UserBase]:
        await self.collection.update_one(
            {"_id":ObjectId(id)},
            {"$set": {**data, "updated_at": datetime.now(timezone.utc())}}
        )
        return await self.find_by_id(id)
    
    async def delete(self, id):
        result = await self.collection.delete_one(
            {"_id":ObjectId(id)})
        return result.deleted_count > 0
        
    async def list(self, skip: int = 0, limit: int = 100) -> List[UserBase]:
        cursor = self.collection.find().skip(skip).limit(limit)
        usuarios = []
        async for documento in cursor:
            usuarios.append(UserBase(documento))
        return usuarios

