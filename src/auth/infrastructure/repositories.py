from auth.domain.entities import User
from auth.interfaces.repositories import UserRepository
from shared.database.mongodb import db
from typing import Optional

class MongoDBUserRepository(UserRepository):
    def __init__(self):
        self.users_collection = db["users"]

    async def get_user_by_username(self, username: str) -> Optional[User]:
        user_data = await self.users_collection.find_one({"username": username})
        if user_data:
            return User(**user_data)
        return None