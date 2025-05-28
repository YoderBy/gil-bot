import motor.motor_asyncio
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

# Create MongoDB client
client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.MONGODB_DB_NAME]

# Create text index for syllabus collection for text search capabilities
async def setup_indexes():
    """Setup MongoDB indexes."""
    # Text index on syllabus title, description and content
    await database.syllabus.create_index([
        ("title", "text"),
        ("description", "text"),
        ("content.topic", "text"),
        ("content.description", "text")
    ])
    
    # Index on sender for messages
    await database.messages.create_index("sender")

async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get database connection."""
    try:
        yield database
    finally:
        # No need to close with motor - client handles connection pool
        pass 