
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.database import db

async def diagnose():
    print(f"Connecting to: {settings.MONGO_CONNECTION_STRING.split('@')[-1]}")
    print(f"Database: {settings.DATABASE_NAME}")
    
    await db.connect()
    database = db.client[settings.DATABASE_NAME]
    
    collections = await database.list_collection_names()
    print(f"\nCollections: {collections}")
    
    for col in collections:
        count = await database[col].count_documents({})
        print(f"  - {col}: {count}")
        
    if "projects" in collections:
        projects = await database.projects.find().to_list(None)
        print(f"\nTotal Projects: {len(projects)}")
        for p in projects:
            print(f"    - Project ID: {p.get('project_id')}, Client: {p.get('client_id')}, Name: {p.get('name')}")
            
    await db.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
