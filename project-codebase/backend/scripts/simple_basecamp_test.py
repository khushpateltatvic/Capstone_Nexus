#!/usr/bin/env python3
"""
Simple Basecamp test - just check if API is accessible
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_basecamp_api():
    """Test basic Basecamp API access"""
    
    # Get config from environment
    access_token = os.getenv("BASECAMP_ACCESS_TOKEN")
    account_id = os.getenv("BASECAMP_ACCOUNT_ID")
    user_agent = os.getenv("BASECAMP_USER_AGENT")
    project_ids = os.getenv("BASECAMP_PROJECT_IDS", "").split(",")
    
    print("🔧 Configuration:")
    print(f"  Access Token: {'✅ Set' if access_token else '❌ Missing'}")
    print(f"  Account ID: {account_id}")
    print(f"  User Agent: {user_agent}")
    print(f"  Project IDs: {project_ids}")
    
    if not access_token or not account_id:
        print("❌ Missing required configuration")
        return
    
    # Test API access
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Content-Type": "application/json"
    }
    
    base_url = "https://3.basecampapi.com"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Get account info
        print("\n🧪 Test 1: Account access")
        try:
            url = f"{base_url}/{account_id}/projects.json"
            print(f"  URL: {url}")
            response = await client.get(url, headers=headers, timeout=30.0)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                projects = response.json()
                print(f"  ✅ Found {len(projects)} projects")
                for project in projects[:3]:  # Show first 3
                    print(f"    - {project.get('name', 'Unknown')} (ID: {project.get('id')})")
            elif response.status_code == 401:
                print("  ❌ Unauthorized - check access token")
            else:
                print(f"  ❌ Error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        # Test 2: Get specific project
        if project_ids and project_ids[0].strip():
            print(f"\n🧪 Test 2: Specific project access")
            try:
                project_id = project_ids[0].strip()
                url = f"{base_url}/{account_id}/projects/{project_id}.json"
                print(f"  URL: {url}")
                response = await client.get(url, headers=headers, timeout=30.0)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    project = response.json()
                    print(f"  ✅ Project: {project.get('name', 'Unknown')}")
                    print(f"  ✅ Description: {project.get('description', 'No description')[:100]}...")
                    
                    # Show dock tools
                    dock = project.get('dock', [])
                    print(f"  ✅ Available tools: {len(dock)}")
                    for tool in dock:
                        enabled = "✅" if tool.get('enabled') else "❌"
                        print(f"    {enabled} {tool.get('name', 'Unknown')}")
                        
                elif response.status_code == 401:
                    print("  ❌ Unauthorized - check access token")
                elif response.status_code == 404:
                    print("  ❌ Project not found - check project ID")
                else:
                    print(f"  ❌ Error: {response.status_code} - {response.text[:200]}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_basecamp_api())