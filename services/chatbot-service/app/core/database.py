from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_USER = os.getenv("MONGO_USER", "csadmin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "cspassword123")
MONGO_DB = os.getenv("MONGO_DB", "csplatform_nosql")

MONGO_URL = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"

_client: AsyncIOMotorClient = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


async def get_db():
    client = get_mongo_client()
    db = client[MONGO_DB]
    yield db
