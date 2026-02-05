#!/usr/bin/env python3
"""
Check what data is actually in the project after extraction
"""

import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

def check_project_data():
    print("Checking project data after extraction...")
    
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
    
    # Check project data
    project_id = "icici_41106708"
    client_id = "icici_lombard"
    
    resp = requests.get(f"{BASE_URL}/api/v1/projects/{client_id}/{project_id}", headers=headers)
    
    if resp.status_code == 200:
        project_data = resp.json()
        print(f"✅ Project data retrieved")
        print(f"   Project: {project_data.get('name', 'Unknown')}")
        
        # Check each section
        sections = ["universal_context", "operations", "technical", "commercial", "strategy", "marketing"]
        
        for section in sections:
            section_data = project_data.get(section, {})
            if isinstance(section_data, dict):
                non_empty_fields = {k: v for k, v in section_data.items() if v}
                print(f"   📊 {section}: {len(non_empty_fields)} populated fields")
                
                # Show some sample data
                if non_empty_fields:
                    for key, value in list(non_empty_fields.items())[:3]:  # Show first 3 fields
                        if isinstance(value, str) and len(value) > 100:
                            value_preview = value[:100] + "..."
                        else:
                            value_preview = str(value)
                        print(f"      - {key}: {value_preview}")
                else:
                    print(f"      (empty)")
            else:
                print(f"   📊 {section}: {section_data}")
        
        # Check other fields
        other_fields = ["created_at", "updated_at", "created_by"]
        for field in other_fields:
            if field in project_data:
                print(f"   📅 {field}: {project_data[field]}")
                
    else:
        print(f"❌ Failed to get project data: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":