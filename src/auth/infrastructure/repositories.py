from src.auth.domain.entities import User
from src.auth.interfaces.repositories import UserRepository
from src.shared.database.mongodb import MongoDB
from typing import Optional

class MongoDBUserRepository(UserRepository):
    """Implementación concreta para MongoDB del repositorio de usuarios"""
    
    def __init__(self, mongo: MongoDB):
        self.mongo = mongo
        self.users_collection = mongo.get_collection("users")

    async def get_user_by_username(self, username: str) -> Optional[User]:
        user_data = await self.users_collection.find_one({"username": username})
        if user_data:
            return User(**user_data)
        return None

    async def create_user(self, user: User) -> User:
        await self.users_collection.insert_one(user.dict())
        return user