import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        await asyncio.wait_for(client.admin.command('ping'), timeout=5.0)
        print("Mongo OK")
    except Exception as e:
        print(f"Mongo Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
