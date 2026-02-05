#!/usr/bin/env python3
"""
Test script to verify Basecamp sync functionality
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ingestion.basecamp import basecamp_service
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('basecamp_test.log')
    ]
)

async def test_basecamp_sync():
    """Test Basecamp sync functionality"""
    print("🚀 === BASECAMP SYNC TEST ===")
    
    # Test 1: Check configuration
    print(f"✅ Basecamp enabled: {basecamp_service.enabled}")
    print(f"✅ Account ID: {basecamp_service.account_id}")
    print(f"✅ Project IDs: {basecamp_service.project_ids}")
    print(f"✅ Has access token: {'Yes' if settings.BASECAMP_ACCESS_TOKEN else 'No'}")
    
    if not basecamp_service.enabled:
        print("❌ Basecamp is not enabled. Check your .env configuration.")
        return
    
    # Test 2: Try to sync one project (incremental)
    print("\n🔄 Testing incremental sync...")
    try:
        results = await basecamp_service.sync_all_projects(full_sync=False)
        print(f"✅ Sync results: {results}")
        
        if results.get("documents"):
            print(f"📄 Found {len(results['documents'])} documents with updates")
            for doc in results["documents"]:
                print(f"  - {doc['project_name']} ({doc['project_id']})")
        else:
            print("📄 No documents with updates found")
            
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check sync states
    print("\n📅 Checking sync states...")
    try:
        for project_id in basecamp_service.project_ids:
            last_sync = await basecamp_service.get_last_sync_time(project_id)
            print(f"  - Project {project_id}: {last_sync.isoformat() if last_sync else 'Never synced'}")
    except Exception as e:
        print(f"❌ Error checking sync states: {e}")

if __name__ == "__main__":
    asyncio.run(test_basecamp_sync())