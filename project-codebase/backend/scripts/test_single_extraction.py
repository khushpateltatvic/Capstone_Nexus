#!/usr/bin/env python3
"""
Test single project extraction to verify the fix
"""

import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

def test_extraction():
    print("Testing single project extraction...")
    
    # Login
    login_data = {"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login/access-token", data=login_data)
    
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.status_code}")
        return
    
    token = resp.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test extraction for one project
    extraction_payload = {
        "client_id": "icici_lombard",
        "project_id": "icici_41106708",
        "project_name": "[ICICI Lombard] [Marketing Concierge Essential] [MS - T & M]"
    }
    
    print(f"Testing extraction for: {extraction_payload['project_name']}")
    
    resp = requests.post(f"{BASE_URL}/api/v1/automation/extract", json=extraction_payload, headers=headers)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Success!")
        print(f"   Sections extracted: {len(data.get('sections_extracted', []))}")
        print(f"   Fields updated: {data.get('fields_updated', 0)}")
        if data.get('sections_extracted'):
            print(f"   Sections: {', '.join(data.get('sections_extracted', []))}")
    else:
        print(f"❌ Failed ({resp.status_code}): {resp.text}")

if __name__ == "__main__":
    test_extraction()