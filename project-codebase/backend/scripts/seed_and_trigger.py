
import requests
import json
from datetime import datetime, timezone

# --- Configuration ---
# Set these to match your actual server environment
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

# Client Data
CLIENT_PAYLOAD = {
    "client_id": "icici_lombard",
    "name": "ICICI Lombard",
    "industry": "Insurance",
    "notes": "Automated seed client"
}

# Official Project Data
OFFICIAL_PROJECTS = [
    {
        "project_id": "icici_001",
        "client_id": "icici_lombard",
        "name": "ICICI Lombard Concierge Essential MS-T&M",
    },
    {
        "project_id": "icici_002",
        "client_id": "icici_lombard",
        "name": "ICICI Lombard GA4 Readiness Google Funded MS-T&M",
    },
    {
        "project_id": "icici_003",
        "client_id": "icici_lombard",
        "name": "ICICI Lombard GA Consulting MS-T&M",
    },
    {
        "project_id": "icici_004",
        "client_id": "icici_lombard",
        "name": "ICICI Lombard Marketing Concierge Essential MS-T&M",
    }
]

# User's Input Targets (Simulating typos)
TARGETS = [
    "icic lombard cocierige essential ms - t & m",   
    "icici lombard ga4 readiness google funded ms - t & m",
    "icici lombard ga consulting ms - t & m",
    "icici lombard marketing conceirge essential ms - t & m"
]

def run_script():
    print("\n" + "="*50)
    print(" PROJECT NEXUS: CLIENT-FIRST SEED & TEST")
    print("="*50)
    
    # 1. Login
    print("\n[Step 1] Authenticating...")
    login_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/auth/login/access-token", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Login failed ({resp.status_code}): {resp.text}")
            return
            
        token = resp.json().get("access_token")
        if not token:
            print("❌ No token received.")
            return

        print(f"✅ Login successful for {ADMIN_EMAIL}")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return

    # 2. Create Client (Explicitly First)
    print("\n[Step 2] Creating Client Entity...")
    try:
        r = requests.post(f"{BASE_URL}/api/v1/clients", json=CLIENT_PAYLOAD, headers=headers)
        if r.status_code == 201:
            print(f"   ✅ Created Client: '{CLIENT_PAYLOAD['name']}'")
        elif r.status_code == 400 and "already exists" in r.text:
            print(f"   ℹ️  Client Exists: '{CLIENT_PAYLOAD['name']}'")
        else:
            print(f"   ❌ Failed to create client: {r.status_code} {r.text}")
    except Exception as e:
        print(f"   ❌ Error checking client: {e}")

    # 3. Create Projects & Ingest Dummy Data
    print("\n[Step 3] Creating Projects & Ingesting Data...")
    for proj in OFFICIAL_PROJECTS:
        proj["assigned_users"] = [ADMIN_EMAIL]
        # Create Project
        try:
            r = requests.post(f"{BASE_URL}/api/v1/projects", json=proj, headers=headers)
            if r.status_code == 201:
                print(f"   ✅ Created: '{proj['name']}'")
            elif r.status_code == 400 and "already exists" in r.text:
                print(f"   ℹ️  Exists:  '{proj['name']}'")
            else:
                print(f"   ⚠️  Warning ({r.status_code}): {r.text}")
        except Exception as e:
            print(f"   ❌ Error seeding project: {e}")

        # Ingest Dummy Data (To prevent empty extraction results)
        ingest_payload = {
            "text": f"This is a sample project document for {proj['name']}. It involves comprehensive analysis and implementation of {proj.get('department', 'general')} strategies for the client {proj.get('client_id')}. The project status is Green. The goal is to improve operational efficiency and deliver high-quality results by Q4 2026.",
            "metadata": {
                "client_id": proj["client_id"],
                "project_id": proj["project_id"],
                "filename": "seed_data.txt"
            }
        }
        try:
            r_ingest = requests.post(f"{BASE_URL}/api/v1/automation/ingest", json=ingest_payload, headers=headers)
            if r_ingest.status_code == 200:
                print(f"      📄 Ingested data for: '{proj['name']}'")
            else:
                print(f"      ⚠️ Ingest Failed: {r_ingest.text}")
        except Exception as e:
             print(f"      ❌ Ingest Error: {e}")


    # 4. Test Extraction
    print("\n[Step 4] Verifying Extraction Logic...")
    success_count = 0
    for name in TARGETS:
        print(f"\n   🔍 Triggering Extraction: '{name}'")
        payload = {"project_name": name}
        try:
            r = requests.post(f"{BASE_URL}/api/v1/automation/extract", json=payload, headers=headers)
            if r.status_code == 200:
                data = r.json()
                print(f"      🎉 Success! Resolved to {data.get('project_id')} / {data.get('client_id')}")
                print(f"          Extracted Sections: {len(data.get('sections_extracted', []))}")
                success_count += 1
            else:
                print(f"      ❌ Failed ({r.status_code}): {r.json().get('detail')}")
        except Exception as e:
            print(f"      ❌ Request Error: {e}")

    print("\n" + "="*50)
    print(f" FINAL RESULT: {success_count}/{len(TARGETS)} Tests Passed")
    print("="*50)

if __name__ == "__main__":
    run_script()
