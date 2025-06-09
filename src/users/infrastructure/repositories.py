from dataclasses import asdict
from bson import ObjectId
from base64 import b64encode
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorCollection
from ..domain.models import UserBase, MFAConfig
from ..domain.ports import UserRepository
import logging

logger = logging.getLogger(__name__)

class DBUserRepository(UserRepository):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def find_by_id(self, id: str) -> UserBase | None:
        user_data = await self.collection.find_one({"_id": ObjectId(id)})
        return UserBase.from_mongo(user_data) if user_data else None

    async def find_by_id_microsoft(self, id: str):
        user_data = await self.collection.find_one({"microsoft_id_account": id})
        return UserBase.from_mongo(user_data) if user_data else None

    async def find_by_email(self, email: str) -> UserBase | None:
        user_data = await self.collection.find_one({"email": email})
        return UserBase.from_mongo(user_data) if user_data else None

    async def create(self, user: UserBase) -> UserBase | None:
        data = asdict(user)
        data.pop("_id", None)
        if "auth_provider" in data and hasattr(data["auth_provider"], "value"):
            data["auth_provider"] = data["auth_provider"].value
        result = await self.collection.insert_one(data)
        user._id = str(result.inserted_id)
        return user

    async def update(self, email: str, data: dict) -> bool:
        await self.collection.update_one(
            {"_id": ObjectId(email)},
            {"$set": {**data, "updated_at": datetime.now(timezone.utc)}},
        )
        return await self.find_by_id(id =email)
    
    async def change_password(self, email:str, data:dict) -> bool:
        result = await self.collection.update_one(
            {"email": email},
            {"$set": {**data, "updated_at": datetime.now(timezone.utc)}},
        )

        return result.modified_count> 0

    async def delete(self, id:str) -> None:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    async def list(self, page: int = 0, per_page: int = 10) -> Tuple[List[UserBase], int]:
        skip =  0 if page <= 0 else (page - 1) * per_page
        cursor = self.collection.find({}).skip(skip).limit(per_page)
 
        usuarios = [UserBase.from_mongo(document) async for document in cursor]

        total = await self.collection.count_documents({})
        
        return usuarios, total

    async def find_by_username(self, username: str) -> UserBase | None:
        user_data = await self.collection.find_one({"username": username})
        if not user_data:
            return None

        # Asegurar que mfa existe como diccionario
        if "mfa" not in user_data:
            user_data["mfa"] = asdict(MFAConfig())

        # Convertir a UserBase
        try:
            return UserBase.from_mongo(user_data)
        except Exception as e:
            logger.error(f"Error convirtiendo usuario desde MongoDB: {str(e)}")
            raise

    async def update_user_mfa(self, username: str, mfa_config: MFAConfig) -> bool:
        result = await self.collection.update_one(
            {"username": username},
            {
                "$set": {
                    "mfa": asdict(mfa_config),
                    "updated_at": datetime.now(
                        timezone.utc
                    ),  
                }
            },
        )
        return result.modified_count > 0
    
    async def image_to_b64(self, img:str)->str:
        try:
            with open(img,"rb") as image:
                img_data = image.read()
                img_b64 = b64encode(img_data).decode("utf-8")
                return img_b64
        except FileNotFoundError as e:
            print(f"Error: no se encontro el archivo {e}")
            return ""
