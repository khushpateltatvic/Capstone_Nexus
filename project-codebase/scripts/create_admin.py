import asyncio
import sys
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.database import db
from app.core.security import get_password_hash
from app.models.domain.user import User

async def create_admin():
    print("Connecting to DB...")
    await db.connect()
    database = db.db
    
    email = "admin@example.com"
    password = "password123" # Change this!
    
    print(f"Checking for existing user: {email}")
    existing = await database.users.find_one({"email": email})
    if existing:
        print("✅ Admin user already exists.")
    else:
        print("Creating new admin user...")
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name="System Admin",
            is_superuser=True
        )
        await database.users.insert_one(user.dict())
        print(f"✅ Created admin user: {email} / {password}")
        
    await db.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_admin())
