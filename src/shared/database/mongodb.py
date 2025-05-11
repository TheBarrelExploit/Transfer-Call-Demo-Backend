import logging
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
)
from pymongo.errors import ConnectionFailure
from typing import Optional


logger = logging.getLogger(__name__)


class MongoDB:
    """
    mongoDB connection manager
    """

    _instance: Optional["MongoDB"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
            cls._client = None
            cls._db = None
        return cls._instance

    async def connect(self, uri: str, db_name: str):
        """
        connect to mongoDB
        """
        if self._client is None:
            try:
                logger.info("connecting to MongoDB...")
                self._client = AsyncIOMotorClient(uri, maxPoolSize=10)

                await self._client.admin.command("ping")
                logger.info("MongoDB connected")

                self._db = self._client[db_name]
            except ConnectionFailure as e:
                logger.error(f"MongoDB connection failed: {e}")
                raise
        else:
            logger.warning("MongoDB already connected")

    def get_database(self) -> AsyncIOMotorDatabase:
        """get database from mongoDB

        Raises:
            ConnectionError: Connection not successful to mongoDB

        Returns:
            AsyncIOMotorDatabase: database mongoDB
        """

        if self._db is None:
            raise ConnectionError("MongoDB not connected")
        return self._db

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """
        get collection from mongoDB
        """
        if self._db is None:
            raise ConnectionError("MongoDB not connected")
        return self._db[collection_name]

    async def close(self):
        """
        close mongoDB connection
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")
