#!/usr/bin/env python3
"""
List all projects to see what exists
"""

import requests
import json

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

def list_projects():
    print("Listing all projects...")
    
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
    
    # List projects for icici_lombard client
    resp = requests.get(f"{BASE_URL}/api/v1/projects/icici_lombard", headers=headers)
    
    if resp.status_code == 200:
        projects = resp.json()
        print(f"✅ Found {len(projects)} projects for icici_lombard:")
        
        for project in projects:
            print(f"   📋 {project.get('project_id', 'Unknown ID')}")
            print(f"      Name: {project.get('name', 'Unknown')}")
            print(f"      Created: {project.get('created_at', 'Unknown')}")
            print(f"      Updated: {project.get('updated_at', 'Unknown')}")
            
            # Check if sections are populated
            sections = ["universal_context", "operations", "technical", "commercial", "strategy", "marketing"]
            populated_sections = []
            
            for section in sections:
                section_data = project.get(section, {})
                if isinstance(section_data, dict) and any(section_data.values()):
                    populated_sections.append(section)
            
            print(f"      Populated sections: {len(populated_sections)}/{len(sections)}")
            if populated_sections:
                print(f"      Sections: {', '.join(populated_sections)}")
            print()
                
    else:
        print(f"❌ Failed to list projects: {resp.status_code}")
        print(resp.text)

if __name__ == "__main__":
    list_projects()