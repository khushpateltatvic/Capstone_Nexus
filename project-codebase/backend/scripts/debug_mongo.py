
import asyncio
from app.core.database import db, get_database

async def debug_mongo():
    await db.connect()
    database = await get_database()
    
    # Check all projects
    projects = await database.projects.find().to_list(None)
    print(f"\nFound {len(projects)} projects")
    
    for p in projects:
        print(f"\n--- Project: {p.get('project_id')} ---")
        import json
        from bson import json_util
        print(json.dumps(p, indent=2, default=json_util.default))
        break # Just one for deep inspection

    await db.close()

if __name__ == "__main__":
    asyncio.run(debug_mongo())
