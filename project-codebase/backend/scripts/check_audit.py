
import asyncio
from app.core.database import db, get_database

async def check_audit():
    await db.connect()
    database = await get_database()
    log = await database.metadata.find_one({"event": "production_reduction_complete"}, sort=[("timestamp", -1)])
    if log:
        print(f"Log for project {log.get('project_id')}")
        print(f"Fields updated: {log.get('fields_updated')}")
    else:
        print("No audit log found.")
    await db.close()

if __name__ == "__main__":
    asyncio.run(check_audit())
