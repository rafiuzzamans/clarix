from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = (
    f"mongodb://{os.getenv('MONGO_USER','csadmin')}:{os.getenv('MONGO_PASSWORD','cspassword123')}"
    f"@{os.getenv('MONGO_HOST','localhost')}:{os.getenv('MONGO_PORT','27017')}"
)
MONGO_DB = os.getenv("MONGO_DB", "csplatform_nosql")

_client = None


def get_mongo_client():
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


async def get_db():
    yield get_mongo_client()[MONGO_DB]
