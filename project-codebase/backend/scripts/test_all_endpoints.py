#!/usr/bin/env python3
"""
Comprehensive API Test Script for Project Nexus

Tests ALL API endpoints with actual requests.
Uses ravi@tatvic.com / Admin@123 for authentication.

Usage:
    cd backend
    uvicorn app.main:app --port 8000  # Start server first
    python scripts/test_all_endpoints.py
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {"email": "ravi@tatvic.com", "password": "Admin@123"}

# Test data
TEST_CLIENT_ID = "test_corp_api"
TEST_PROJECT_ID = "test_project_api"


class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _log_result(self, method: str, endpoint: str, status: int, success: bool, detail: str = ""):
        result = {
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "success": success,
            "detail": detail
        }
        self.results.append(result)
        if success:
            self.passed += 1
            print(f"  ✅ {method} {endpoint} -> {status}")
        else:
            self.failed += 1
            print(f"  ❌ {method} {endpoint} -> {status} | {detail}")
    
    def _get(self, endpoint: str, expected_status: int = 200) -> Optional[Dict]:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", headers=self._headers(), timeout=60)
            success = resp.status_code == expected_status
            self._log_result("GET", endpoint, resp.status_code, success)
            return resp.json() if resp.status_code < 400 else None
        except Exception as e:
            self._log_result("GET", endpoint, 0, False, str(e))
            return None
    
    def _post(self, endpoint: str, data: Dict = None, expected_status: int = 200, is_form=False) -> Optional[Dict]:
        try:
            url = f"{BASE_URL}{endpoint}"
            if is_form:
                resp = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=60)
            else:
                resp = requests.post(url, json=data or {}, headers=self._headers(), timeout=60)
            
            success = resp.status_code == expected_status
            self._log_result("POST", endpoint, resp.status_code, success)
            return resp.json() if resp.status_code < 400 else None
        except Exception as e:
            self._log_result("POST", endpoint, 0, False, str(e))
            return None
    
    def _put(self, endpoint: str, data: Dict = None, expected_status: int = 200) -> Optional[Dict]:
        try:
            resp = requests.put(f"{BASE_URL}{endpoint}", headers=self._headers(), json=data or {}, timeout=60)
            success = resp.status_code == expected_status
            self._log_result("PUT", endpoint, resp.status_code, success)
            return resp.json() if resp.status_code < 400 else None
        except Exception as e:
            self._log_result("PUT", endpoint, 0, False, str(e))
            return None
    
    def _delete(self, endpoint: str, expected_status: int = 200) -> bool:
        try:
            resp = requests.delete(f"{BASE_URL}{endpoint}", headers=self._headers(), timeout=60)
            success = resp.status_code == expected_status
            self._log_result("DELETE", endpoint, resp.status_code, success)
            return success
        except Exception as e:
            self._log_result("DELETE", endpoint, 0, False, str(e))
            return False

    # ==================== AUTH ====================
    def test_auth(self):
        print("\n" + "="*50)
        print("🔐 TESTING AUTH ENDPOINTS")
        print("="*50)
        
        # Login with retry
        print("\n📍 Login...")
        login_data = {"username": TEST_USER["email"], "password": TEST_USER["password"]}
        
        max_retries = 3
        for attempt in range(max_retries):
            print(f"   Attempt {attempt+1}/{max_retries}...")
            login_resp = self._post("/auth/login/access-token", data=login_data, is_form=True)
            if login_resp:
                self.token = login_resp.get("access_token")
                print(f"     Token obtained: {self.token[:30]}...")
                break
            time.sleep(2)
        else:
            print("   ❌ Login failed after all retries")
            return False
        
        # Get current user
        print("\n📍 Get Current User...")
        self._get("/auth/me")
        
        return True

    # ==================== CLIENTS ====================
    def test_clients(self):
        print("\n" + "="*50)
        print("👥 TESTING CLIENTS ENDPOINTS")
        print("="*50)
        
        # Create client
        print("\n📍 Create Client...")
        self._post("/clients", {
            "client_id": TEST_CLIENT_ID,
            "name": "Test Corporation",
            "industry": "Technology",
            "website": "https://test.com"
        }, expected_status=201)
        
        # List clients
        print("\n📍 List Clients...")
        self._get("/clients")
        
        # Get specific client
        print("\n📍 Get Client...")
        self._get(f"/clients/{TEST_CLIENT_ID}")
        
        # Update client
        print("\n📍 Update Client...")
        self._put(f"/clients/{TEST_CLIENT_ID}", {
            "name": "Test Corporation Updated",
            "industry": "Tech & AI"
        })

    # ==================== PROJECTS ====================
    def test_projects(self):
        print("\n" + "="*50)
        print("📁 TESTING PROJECTS ENDPOINTS")
        print("="*50)
        
        # Create project
        # Create project
        print("\n📍 Create Project...")
        self._post("/projects", {
            "client_id": TEST_CLIENT_ID,
            "project_id": TEST_PROJECT_ID,
            "name": "Test Project",
            "status": "active",
            "description": "Auto-generated test project",
            "department": "Engineering"
        }, expected_status=201)
        
        # List projects for client
        print("\n📍 List Projects...")
        self._get(f"/projects/{TEST_CLIENT_ID}")
        
        # Get specific project
        print("\n📍 Get Project...")
        self._get(f"/projects/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}")
        
        # Update project
        print("\n📍 Update Project...")
        self._put(f"/projects/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
            "name": "Test Project Updated",
            "status": "in_progress"
        })

    # ==================== SECTIONS ====================
    def test_sections(self):
        print("\n" + "="*50)
        print("📋 TESTING SECTION ENDPOINTS")
        print("="*50)
        
        sections = [
            "universal-context",
            "operations",
            "technical",
            "commercial",
            "strategy",
            "marketing",
            "other"
        ]
        
        for section in sections:
            print(f"\n📍 Testing /{section}...")
            
            # Get section
            self._get(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}")
            
            # Update section (different payloads per section)
            if section == "universal-context":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "account_summary": "Test account summary from API test"
                })
            elif section == "operations":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "traffic_light": "green"
                })
            elif section == "technical":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "tech_stack": ["Python", "FastAPI", "MongoDB"]
                })
            elif section == "commercial":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "contract_value": 50000
                })
            elif section == "strategy":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "goals": ["Q1 Launch", "Scale to 10k users"]
                })
            elif section == "marketing":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "brand_guidelines": "Use blue color scheme"
                })
            elif section == "other":
                self._put(f"/{section}/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", {
                    "notes": "Test notes from API"
                })

    # ==================== DASHBOARD ====================
    def test_dashboard(self):
        print("\n" + "="*50)
        print("📊 TESTING DASHBOARD ENDPOINTS")
        print("="*50)
        
        print("\n📍 Dashboard Summary...")
        print("\n📍 Dashboard Summary...")
        self._get(f"/dashboard/{TEST_CLIENT_ID}/dashboard")
        
        print("\n📍 Dashboard Ops...")
        self._get(f"/dashboard/{TEST_CLIENT_ID}/operations")

    # ==================== AUTOMATION ====================
    def test_automation(self):
        print("\n" + "="*50)
        print("🤖 TESTING AUTOMATION ENDPOINTS")
        print("="*50)
        
        # Basecamp status
        print("\n📍 Basecamp Status...")
        self._get("/automation/basecamp/status")
        
        # Note: We won't trigger actual sync as it takes time
        # But we test the endpoint exists
        print("\n📍 Sync endpoint (checking availability)...")
        self._post("/automation/sync")

        # Ingest Status
        print("\n📍 Ingest Status...")
        self._get("/automation/ingest/status")

        # Extract All
        print("\n📍 Extract All projects...")
        self._post("/automation/extract-all")

    # ==================== INGEST ====================
    def test_ingest(self):
        print("\n" + "="*50)
        print("📥 TESTING INGEST ENDPOINTS")
        print("="*50)
        
        print("\n📍 Processing Status...")
        self._get("/ingest/status", expected_status=404) # Check if it's moved

    # ==================== CLEANUP ====================
    def setup_cleanup(self):
        print("\n" + "="*50)
        print("🧹 SETUP CLEANUP (Silent)")
        print("="*50)
        
        # Use direct requests to avoid polluting stats with 404s
        try:
            requests.delete(f"{BASE_URL}/projects/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}", headers=self._headers(), timeout=60)
            requests.delete(f"{BASE_URL}/clients/{TEST_CLIENT_ID}", headers=self._headers(), timeout=60)
            print("   Old test data cleaned up (if any).")
        except Exception:
            pass

    def teardown(self):
        print("\n" + "="*50)
        print("🧹 TEARDOWN")
        print("="*50)
        
        print("\n📍 Delete Test Project...")
        self._delete(f"/projects/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}")
        
        print("\n📍 Delete Test Client...")
        self._delete(f"/clients/{TEST_CLIENT_ID}")

    # ==================== RUN ALL ====================
    def run_all(self):
        print("╔" + "="*58 + "╗")
        print("║" + " "*12 + "🧪 PROJECT NEXUS API TESTER 🧪" + " "*14 + "║")
        print("╚" + "="*58 + "╝")
        print(f"\n🌐 Base URL: {BASE_URL}")
        print(f"👤 Test User: {TEST_USER['email']}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start = time.time()
        
        # Run tests
        if not self.test_auth():
            print("\n❌ Authentication failed! Cannot continue.")
            return
            
        self.setup_cleanup() # Ensure clean state without errors
        
        self.test_clients()
        self.test_projects()
        self.test_sections()
        self.test_dashboard()
        self.test_automation()
        self.test_ingest()
        self.teardown()
        
        duration = time.time() - start
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Total:  {self.passed + self.failed}")
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"🎯 Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        # Save results
        with open("test_results.json", "w") as f:
            json.dump({
                "summary": {
                    "passed": self.passed,
                    "failed": self.failed,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.results
            }, f, indent=2)
        print(f"\n📁 Results saved to: test_results.json")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all()
