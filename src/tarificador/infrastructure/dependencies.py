from fastapi import Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Annotated
from src.tarificador.domain.ports import CallRepositoryDomain
from src.tarificador.infrastructure.repository import CallRepository
from src.shared.database.mongodb import MongoDB
from src.tarificador.application.services import CallService


def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo


def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()


def get_users_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AsyncIOMotorCollection:
    return db.get_collection("llamadas")


def get_user_repository(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_users_collection)],
) -> CallRepository:
    return CallRepository(collection)


def get_user_service(
    repo: Annotated[CallRepository, Depends(get_user_repository)],
) -> CallService:
    return CallService(repo)
