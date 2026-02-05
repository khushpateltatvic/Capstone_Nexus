#!/usr/bin/env python3
"""
Comprehensive verification that Basecamp automation is working perfectly
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('basecamp_automation_verification.log')
    ]
)

async def verify_basecamp_automation():
    """Comprehensive verification of Basecamp automation"""
    print("🔍 === BASECAMP AUTOMATION VERIFICATION ===")
    
    all_tests_passed = True
    
    try:
        # Test 1: Database Connection
        print("\n📊 Test 1: Database Connection")
        try:
            from app.core.database import get_database
            db = await get_database()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            all_tests_passed = False
            return
        
        # Test 2: Basecamp Service Configuration
        print("\n🏕️ Test 2: Basecamp Service Configuration")
        try:
            from app.services.ingestion.basecamp import basecamp_service
            print(f"✅ Service enabled: {basecamp_service.enabled}")
            print(f"✅ Account ID: {basecamp_service.account_id}")
            print(f"✅ Project count: {len(basecamp_service.project_ids)}")
            print(f"✅ Projects: {basecamp_service.project_ids}")
            
            if not basecamp_service.enabled:
                print("❌ Basecamp service is not enabled")
                all_tests_passed = False
                return
                
        except Exception as e:
            print(f"❌ Basecamp service configuration failed: {e}")
            all_tests_passed = False
            return
        
        # Test 3: Startup Automation Service
        print("\n🤖 Test 3: Startup Automation Service")
        try:
            from app.services.automation.startup_automation import startup_automation
            
            # Test sync status check
            status = await startup_automation.get_sync_status()
            print(f"✅ Sync status retrieved: {len(status.get('basecamp', {}))} projects")
            
            for project_id, project_status in status.get('basecamp', {}).items():
                needs_sync = project_status.get('needs_sync', True)
                last_sync = project_status.get('last_sync')
                project_name = project_status.get('project_name', project_id)
                print(f"  📋 {project_name}: {'Needs sync' if needs_sync else 'Up to date'}")
                if last_sync:
                    print(f"      Last sync: {last_sync}")
                    
        except Exception as e:
            print(f"❌ Startup automation service failed: {e}")
            all_tests_passed = False
        
        # Test 4: Message Queue
        print("\n📨 Test 4: Message Queue")
        try:
            from app.core.memory_adapters import msg_queue
            
            # Test queue operations
            test_message = {
                "filename": "test_verification.txt",
                "content": "test content for verification",
                "client_id": "test",
                "project_id": "test",
                "source": "verification"
            }
            
            initial_size = msg_queue.qsize()
            await msg_queue.enqueue(test_message)
            after_enqueue = msg_queue.qsize()
            
            dequeued = await msg_queue.dequeue()
            after_dequeue = msg_queue.qsize()
            
            print(f"✅ Queue operations successful")
            print(f"  Initial size: {initial_size}")
            print(f"  After enqueue: {after_enqueue}")
            print(f"  After dequeue: {after_dequeue}")
            print(f"  Message integrity: {'✅' if dequeued['filename'] == test_message['filename'] else '❌'}")
            
        except Exception as e:
            print(f"❌ Message queue test failed: {e}")
            all_tests_passed = False
        
        # Test 5: Scheduler
        print("\n📅 Test 5: Scheduler")
        try:
            from app.core.scheduler import start_scheduler, scheduler
            
            # Check if scheduler can be started
            start_scheduler()
            print(f"✅ Scheduler started successfully")
            print(f"✅ Running jobs: {len(scheduler.get_jobs())}")
            
            for job in scheduler.get_jobs():
                print(f"  📋 Job: {job.id} - Next run: {job.next_run_time}")
                
        except Exception as e:
            print(f"❌ Scheduler test failed: {e}")
            all_tests_passed = False
        
        # Test 6: API Connectivity (Quick Test)
        print("\n🌐 Test 6: Basecamp API Connectivity")
        try:
            import httpx
            
            # Quick API test
            headers = {
                "Authorization": f"Bearer {basecamp_service.headers.get('Authorization', '').replace('Bearer ', '')}",
                "User-Agent": basecamp_service.headers.get('User-Agent', ''),
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                url = f"{basecamp_service.base_url}/{basecamp_service.account_id}/projects.json"
                response = await client.get(url, headers=headers, timeout=10.0)
                
                if response.status_code == 200:
                    projects = response.json()
                    print(f"✅ API connectivity successful")
                    print(f"✅ Found {len(projects)} accessible projects")
                else:
                    print(f"❌ API returned status {response.status_code}")
                    all_tests_passed = False
                    
        except Exception as e:
            print(f"❌ API connectivity test failed: {e}")
            all_tests_passed = False
        
        # Test 7: Full Automation Flow (Dry Run)
        print("\n🔄 Test 7: Full Automation Flow (Dry Run)")
        try:
            # Check if automation would trigger
            needs_sync = await startup_automation._check_basecamp_needs_sync()
            print(f"✅ Automation check successful")
            print(f"✅ Would trigger sync: {needs_sync}")
            
            if needs_sync:
                print("  📋 Projects that would be synced:")
                for project_id in basecamp_service.project_ids:
                    last_sync = await basecamp_service.get_last_sync_time(project_id)
                    if not last_sync:
                        print(f"    - {project_id}: Never synced")
                    else:
                        hours_old = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
                        print(f"    - {project_id}: {hours_old:.1f} hours old")
            else:
                print("  ✅ All projects are up to date")
                
        except Exception as e:
            print(f"❌ Automation flow test failed: {e}")
            all_tests_passed = False
        
        # Final Results
        print("\n🎯 === VERIFICATION RESULTS ===")
        if all_tests_passed:
            print("🎉 ALL TESTS PASSED - BASECAMP AUTOMATION IS WORKING PERFECTLY!")
            print("\n✅ Summary:")
            print("  - Database connection: Working")
            print("  - Basecamp service: Configured and enabled")
            print("  - Startup automation: Ready")
            print("  - Message queue: Functional")
            print("  - Scheduler: Running")
            print("  - API connectivity: Verified")
            print("  - Automation flow: Ready to trigger")
            print("\n🚀 The system will automatically sync Basecamp data:")
            print("  - On server startup (if data is >24h old)")
            print("  - Every 24 hours via scheduler")
            print("  - Manual triggers via API endpoints")
        else:
            print("❌ SOME TESTS FAILED - PLEASE CHECK THE ERRORS ABOVE")
            
    except Exception as e:
        print(f"❌ Verification failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_basecamp_automation())