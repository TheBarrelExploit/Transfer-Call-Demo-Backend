from fastapi import Depends, HTTPException, status, Request
from src.shared.database.mongodb import MongoDB
from src.auth.infrastructure.repositories import MongoDBUserRepository
from src.auth.infrastructure.microsoft_sso import MicrosoftSSORepository
from src.auth.application.services import AuthService
from src.auth.application.use_cases import MicrosoftAuthService
from src.users.application.services import UserService
from motor.motor_asyncio import  AsyncIOMotorCollection, AsyncIOMotorDatabase
from src.users.infrastructure.repositories import DBUserRepository
from typing import Annotated
from src.users.domain.ports import UserRepository
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


def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo

def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()

def get_users_collection(db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> AsyncIOMotorCollection:
    return db.get_collection("users")

def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)]) -> UserRepository:
    return DBUserRepository(collection)

def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repo)

async def get_auth_microsoft_repository() -> MicrosoftSSORepository:
    return MicrosoftSSORepository()

async def get_auth_service_sso(user_repo: UserService = Depends(get_user_service), sso_auth: MicrosoftSSORepository= Depends(get_auth_microsoft_repository) ) -> MicrosoftAuthService:
    return MicrosoftAuthService(user_repo, sso_auth)
