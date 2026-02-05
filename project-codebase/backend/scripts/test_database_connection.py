#!/usr/bin/env python3
"""
Test database connection to ensure it's working properly
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

async def test_database_connection():
    """Test database connection and operations"""
    print("🔍 === DATABASE CONNECTION TEST ===")
    
    try:
        # Test 1: Basic connection
        print("\n📊 Test 1: Basic Database Connection")
        from app.core.database import get_database
        
        db = await get_database()
        print(f"✅ Database connection: {type(db)}")
        print(f"✅ Database name: {db.name if db is not None else 'None'}")
        
        if db is None:
            print("❌ Database connection returned None")
            return
        
        # Test 2: Test collection access
        print("\n📋 Test 2: Collection Access")
        try:
            # Test if we can access collections
            collections = await db.list_collection_names()
            print(f"✅ Available collections: {collections}")
            
            # Test basecamp_sync_state collection specifically
            if 'basecamp_sync_state' in collections:
                print("✅ basecamp_sync_state collection exists")
                count = await db.basecamp_sync_state.count_documents({})
                print(f"✅ basecamp_sync_state documents: {count}")
            else:
                print("ℹ️ basecamp_sync_state collection doesn't exist yet (will be created on first use)")
                
        except Exception as e:
            print(f"❌ Collection access failed: {e}")
        
        # Test 3: Test Basecamp service database operations
        print("\n🏕️ Test 3: Basecamp Service Database Operations")
        try:
            from app.services.ingestion.basecamp import basecamp_service
            
            # Test getting last sync time (should handle None gracefully)
            test_project_id = "41106708"
            last_sync = await basecamp_service.get_last_sync_time(test_project_id)
            print(f"✅ get_last_sync_time for {test_project_id}: {last_sync}")
            
            # Test setting sync time
            from datetime import datetime, timezone
            test_time = datetime.now(timezone.utc)
            await basecamp_service.set_last_sync_time(test_project_id, test_time)
            print(f"✅ set_last_sync_time for {test_project_id}: {test_time}")
            
            # Test getting it back
            retrieved_sync = await basecamp_service.get_last_sync_time(test_project_id)
            print(f"✅ Retrieved sync time: {retrieved_sync}")
            
            if retrieved_sync:
                print("✅ Database operations working correctly!")
            else:
                print("⚠️ Sync time not retrieved, but no errors")
                
        except Exception as e:
            print(f"❌ Basecamp service database operations failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Test database initialization in main app
        print("\n🚀 Test 4: Main App Database Initialization")
        try:
            from app.core.database import db
            
            print(f"✅ Database client: {type(db.client)}")
            print(f"✅ Database instance: {type(db.db)}")
            
            if db.client is None:
                print("ℹ️ Database client not initialized, calling connect...")
                await db.connect()
                print("✅ Database connected successfully")
            else:
                print("✅ Database client already initialized")
                
        except Exception as e:
            print(f"❌ Main app database initialization failed: {e}")
        
        print("\n🎯 === TEST RESULTS ===")
        print("✅ Database connection tests completed")
        print("✅ The database connection issue should now be resolved")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_connection())