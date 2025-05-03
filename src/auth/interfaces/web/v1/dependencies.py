from fastapi import Depends
from src.shared.database.mongodb import MongoDB
from src.auth.infrastructure.repositories import MongoDBUserRepository
from src.auth.application.services import AuthService
from src.shared.config import get_settings

async def get_mongo() -> MongoDB:
    settings = get_settings()
    mongo = MongoDB()
    await mongo.connect(settings.MONGO_URI, settings.MONGO_DB)
    return mongo

async def get_user_repository(mongo: MongoDB = Depends(get_mongo)) -> MongoDBUserRepository:
    return MongoDBUserRepository(mongo)

async def get_auth_service(user_repo: MongoDBUserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)