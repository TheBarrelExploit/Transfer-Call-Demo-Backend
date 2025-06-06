# Autores: Denuar Andres Ramos Lezama
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from fastapi import Request, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Annotated
from src.shared.database.mongodb import MongoDB
from src.shared.apscheduler.apscheduler_config import SchedulerConfig
from ..infrastructure.repository import PriceRepository
from ..application.services import PriceService


def get_mongo(request: Request) -> MongoDB:
    return request.app.state.mongo


def get_db(mongo: Annotated[MongoDB, Depends(get_mongo)]) -> AsyncIOMotorDatabase:
    return mongo.get_database()


def get_apscheduler(request: Request) -> SchedulerConfig:
    return request.app.state.scheduler


def get_price_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AsyncIOMotorCollection:
    return db.get_collection("price")


def get_history_price_collection(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> AsyncIOMotorCollection:
    return db.get_collection("price history")


def get_repository_price(
    collection: Annotated[AsyncIOMotorCollection, Depends(get_price_collection)],
    collection_history: Annotated[
        AsyncIOMotorCollection, Depends(get_history_price_collection)
    ],
    scheduler: Annotated[SchedulerConfig, Depends(get_apscheduler)],
) -> PriceRepository:
    return PriceRepository(
        collection=collection,
        collection_history=collection_history,
        scheduler=scheduler,
    )


def get_service_price(
    price: PriceRepository = Depends(get_repository_price),
) -> PriceService:
    return PriceService(price=price)
