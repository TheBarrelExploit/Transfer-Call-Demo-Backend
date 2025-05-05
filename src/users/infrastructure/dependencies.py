from fastapi import Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Annotated
from src.users.domain.ports import UserRepository
from src.users.infrastructure.repositories import DBUserRepository
from src.users.application.services import UserService
from src.shared.database.mongodb import MongoDB

def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo

def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()

def get_users_collection(db: Annotated[AsyncIOMotorDatabase, Depends(get_db)]) -> AsyncIOMotorCollection:
    return db.get_collection("users")

def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)]
) -> UserRepository:
    return DBUserRepository(collection)

def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(repo)






