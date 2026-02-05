import asyncio
from app.core.database import get_database

async def cleanup_db():
    print("🧹 Cleaning up MongoDB for a fresh start...")
    db = await get_database()
    
    # Drop projects and clients for the test client
    # In a real app we'd be more surgical, but for testing wiping is safer.
    await db.projects.delete_many({"client_id": "test_corp_v1"})
    # Also wipe the one without client_id for safety
    await db.projects.delete_many({"client_id": {"$exists": False}})
    
    print("✅ Cleanup complete. Collections are ready.")

if __name__ == "__main__":
    asyncio.run(cleanup_db())
