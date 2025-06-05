# Autores: Denuar Andres Ramos Lezama
# Fecha: Junio 2025
# Proyecto: Demo Tarificador
# Derechos reservados
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import cast
import pytz


class SchedulerConfig:
    def __init__(self, mongo_client: MongoClient, mongo_database_name: str):
        self.mongo_client = mongo_client
        self.mongo_database_name: str = mongo_database_name

        self.db: Database = self.mongo_client[self.mongo_database_name]

        self.prices_changes: Collection = cast(Collection, self.db["prices_changes"])

        self.scheduler = AsyncIOScheduler(
            jobstores={
                "default": MongoDBJobStore(
                    database=self.mongo_database_name,
                    collection="jobs",
                    client=self.mongo_client,
                )
            },
            executor={"default": AsyncIOExecutor()},
            job_defaults={"coalesce": False, "max_instances": 3},
            timezone=pytz.utc,
        )

    def start(self):
        self.scheduler.start()

    def shutdowm(self):
        self.scheduler.shutdown()
