
import requests

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

def verify():
    # Login
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login/access-token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Hardest Case
    target = "icici lombard ga consulting ms - t & m"
    print(f"Testing: '{target}'")
    
    r = requests.post(f"{BASE_URL}/api/v1/automation/extract", json={"project_name": target}, headers=headers)
    
    if r.status_code == 200:
        print(f"✅ SUCCESS! Resolved to: {r.json().get('resolved_name')}")
    else:
        print(f"❌ FAILED: {r.text}")

if __name__ == "__main__":
    verify()
