
import asyncio
import json
from bson import json_util
from app.core.database import db, get_database

async def check():
    await db.connect()
    database = await get_database()
    projects = await database.projects.find({"client_id": "test_corp_v1"}).to_list(None)
    print(f"Found {len(projects)} projects for test_corp_v1")
    for p in projects:
        print(json.dumps(p, indent=2, default=json_util.default))
    await db.close()

if __name__ == "__main__":
    asyncio.run(check())
