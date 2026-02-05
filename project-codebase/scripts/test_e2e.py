"""
End-to-End Test Script for Hybrid RAG Pipeline

This script tests the new two-phase data extraction flow:
1. PHASE 1: Ingest all documents (chunk + embed + store in ChromaDB)
2. PHASE 2: Extract all sections using RAG queries
"""

import asyncio
import httpx
import logging
import os
import sys
import random
from pathlib import Path
# Add backend directory to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.resolve()))

from app.tests.mock_data_generator import MockDataGenerator

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("E2E-Test")

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_SECRET = "your_super_secret_random_hex_string_here"

# Test credentials
TEST_EMAIL = f"tester_{random.randint(1000000000, 9999999999)}@example.com"
TEST_PASSWORD = "TestPassword123!"
TEST_CLIENT_ID = "test_corp_v1"
TEST_PROJECT_ID = "p_nexus_e2e"


async def run_e2e_test():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Register
        logger.info(f"Step 1: Registering user {TEST_EMAIL}...")
        reg_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            headers={"X-Admin-Secret": ADMIN_SECRET}
        )
        if reg_response.status_code != 200:
            logger.error(f"Registration failed: {reg_response.text}")
            return
        
        # Step 2: Login
        logger.info("Step 2: Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login/access-token",
            data={"username": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if login_response.status_code != 200:
            logger.error(f"Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Clear existing vectors
        logger.info("Step 3: Clearing existing vectors...")
        await client.delete(
            f"{BASE_URL}/automation/clear/{TEST_CLIENT_ID}/{TEST_PROJECT_ID}",
            headers=headers
        )
        
        # Step 4: Generate and Ingest mock data (PHASE 1)
        logger.info("Step 4: PHASE 1 - Ingesting documents into vector store...")
        payloads = MockDataGenerator.get_all_test_payloads(TEST_CLIENT_ID, TEST_PROJECT_ID)
        
        documents = []
        for payload in payloads:
            documents.append({
                "text": payload["text"],
                "metadata": {
                    "filename": payload["filename"],
                    "client_id": TEST_CLIENT_ID,
                    "project_id": TEST_PROJECT_ID
                }
            })
            logger.info(f"  - Prepared: {payload['filename']}")
        
        # Batch ingest
        ingest_response = await client.post(
            f"{BASE_URL}/automation/ingest-batch",
            json={
                "documents": documents,
                "client_id": TEST_CLIENT_ID,
                "project_id": TEST_PROJECT_ID
            },
            headers=headers
        )
        
        if ingest_response.status_code != 200:
            logger.error(f"Batch ingestion failed: {ingest_response.text}")
            return
        
        ingest_result = ingest_response.json()
        logger.info(f"✅ Ingested {ingest_result.get('documents_processed')} documents, {ingest_result.get('total_chunks_stored')} chunks")
        
        # Step 5: Run RAG extraction (PHASE 2)
        logger.info("Step 5: PHASE 2 - Running RAG extraction for all sections...")
        
        extract_response = await client.post(
            f"{BASE_URL}/automation/extract",
            json={
                "client_id": TEST_CLIENT_ID,
                "project_id": TEST_PROJECT_ID
            },
            headers=headers
        )
        
        if extract_response.status_code != 200:
            logger.error(f"Extraction failed: {extract_response.text}")
            return
        
        extract_result = extract_response.json()
        logger.info(f"✅ Extracted sections: {extract_result.get('sections_extracted')}")
        logger.info(f"✅ Fields updated: {extract_result.get('fields_updated')}")
        
        # Step 6: Verify data in Dashboard
        logger.info("Step 6: Verifying data in Dashboard...")
        
        dashboard_response = await client.get(
            f"{BASE_URL}/dashboard/{TEST_CLIENT_ID}/dashboard",
            headers=headers
        )
        
        if dashboard_response.status_code != 200:
            logger.error(f"Dashboard fetch failed: {dashboard_response.text}")
            return
        
        dashboard_data = dashboard_response.json()
        projects = dashboard_data.get("projects", [])
        
        if not projects:
            logger.error("❌ FAILED: No projects found in dashboard")
            return
        
        project = projects[0]
        logger.info(f"✅ SUCCESS: Project '{project.get('project_id')}' found")
        
        # Verify sections
        universal = project.get("universal_context") or {}
        operations = project.get("operations") or {}
        technical = project.get("technical") or {}
        commercial = project.get("commercial") or {}
        strategy = project.get("strategy") or {}
        marketing = project.get("marketing") or {}
        
        # Summary checks
        checks = {
            "Summary": universal.get("summary"),
            "POC Map": universal.get("poc_map"),
            "Timeline": universal.get("timeline"),
            "Traffic Light": operations.get("traffic_light"),
            "Tasks": operations.get("task_board_upcoming"),
            "Blockers": operations.get("blockers"),
            "Tech Stack": technical.get("tech_stack"),
            "Active SOW": commercial.get("active_sow"),
            "Invoices": commercial.get("invoices"),
            "Goals": strategy.get("goals_roadmap"),
            "Stakeholders": strategy.get("stakeholder_map"),
            "Competitors": strategy.get("competitors"),
            "Brand Guidelines": marketing.get("brand_guidelines"),
        }
        
        logger.info("\n📊 EXTRACTION RESULTS:")
        logger.info("=" * 50)
        
        populated = 0
        for field, value in checks.items():
            if value:
                # Check if it's a datapoint with value
                if isinstance(value, dict) and value.get("value"):
                    logger.info(f"✅ {field}: POPULATED")
                    populated += 1
                elif isinstance(value, list) and len(value) > 0:
                    logger.info(f"✅ {field}: POPULATED ({len(value)} items)")
                    populated += 1
                else:
                    logger.info(f"⚠️  {field}: Has structure but may be empty")
            else:
                logger.info(f"❌ {field}: EMPTY")
        
        logger.info("=" * 50)
        logger.info(f"📈 TOTAL: {populated}/{len(checks)} fields populated")
        
        if populated >= 8:
            logger.info("\n🎉 SUCCESS: RAG Pipeline working correctly!")
        else:
            logger.info("\n⚠️  PARTIAL: Some fields still empty, check agent prompts")


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
