from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz


class SchedulerConfig:
    def __init__(self, mongo_client, mongo_database):
        self.mongo_client = mongo_client
        self.mongo_database = mongo_database
        self.scheduler = AsyncIOScheduler(
            jobstores={
                "default": MongoDBJobStore(
                    database=self.mongo_database,
                    collection="jobs",
                    client=self.mongo_client,
                )
            },
            executor={"default": ThreadPoolExecutor(20)},
            job_defaults={"coalesce": False, "max_instances": 3},
            timezone=pytz.utc,
        )

    def start(self):
        self.scheduler.start()

    def shutdowm(self):
        self.scheduler.shutdown()
