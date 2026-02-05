from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

class Database:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        logging.info("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.MONGO_CONNECTION_STRING)
        self.db = self.client[settings.DATABASE_NAME]
        logging.info("Connected to MongoDB.")
        
        # Ensure indexes (basic example, more complex indexes in initialization script)
        # await self.db.metadata.create_index("file_hash", unique=True)

    async def close(self):
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

db = Database()

async def get_database():
    """Get database connection, ensuring it's connected."""
    if db.db is None:
        logging.info("Database not connected, connecting now...")
        await db.connect()
    return db.db
