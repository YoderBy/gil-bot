import motor.motor_asyncio
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.MONGODB_DB_NAME]

async def setup_indexes():
    """Setup MongoDB indexes."""
    await database.syllabus.create_index([
        ("title", "text"),
        ("description", "text"),
        ("content.topic", "text"),
        ("content.description", "text")
    ])
    
    await database.messages.create_index("sender")

async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get database connection."""
    try:
        yield database
    finally:
        # No need to close with motor - client handles connection pool
        pass 