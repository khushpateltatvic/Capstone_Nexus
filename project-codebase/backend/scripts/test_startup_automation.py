#!/usr/bin/env python3
"""
Test startup automation to ensure it works correctly
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
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup_automation_test.log')
    ]
)

async def test_startup_automation():
    """Test the startup automation functionality"""
    print("🚀 === STARTUP AUTOMATION TEST ===")
    
    try:
        # Initialize database connection first
        from app.core.database import get_database
        db = await get_database()
        print("✅ Database connection established")
        
        # Test startup automation
        from app.services.automation.startup_automation import startup_automation
        
        print("🤖 Running startup automation check...")
        results = await startup_automation.check_and_run_automation()
        
        print(f"📊 Results: {results}")
        
        if results.get("error"):
            print(f"❌ Error: {results['error']}")
        else:
            print(f"✅ Basecamp triggered: {results.get('basecamp_triggered', False)}")
            print(f"✅ Watchdog triggered: {results.get('watchdog_triggered', False)}")
            
            if results.get("basecamp_results"):
                br = results["basecamp_results"]
                print(f"📋 Basecamp results:")
                print(f"  - Successful: {len(br.get('successful_projects', []))}")
                print(f"  - Failed: {len(br.get('failed_projects', []))}")
                print(f"  - Documents queued: {br.get('documents_queued', 0)}")
        
        # Test scheduler
        print("\n📅 Testing scheduler...")
        from app.core.scheduler import start_scheduler
        start_scheduler()
        print("✅ Scheduler started successfully")
        
        # Test message queue
        print("\n📨 Testing message queue...")
        from app.core.memory_adapters import msg_queue
        
        test_message = {
            "filename": "test.txt",
            "content": "test content",
            "client_id": "test",
            "project_id": "test",
            "source": "test"
        }
        
        await msg_queue.enqueue(test_message)
        print(f"✅ Message queued. Queue size: {msg_queue.qsize()}")
        
        dequeued = await msg_queue.dequeue()
        print(f"✅ Message dequeued: {dequeued['filename']}")
        
        print("\n🎉 === ALL TESTS PASSED ===")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup_automation())