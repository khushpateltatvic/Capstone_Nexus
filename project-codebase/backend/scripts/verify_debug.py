
import requests

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "ravi@tatvic.com"
ADMIN_PASSWORD = "Admin@123"

def debug():
    print("--- Debugging Extraction Failure ---")
    
    # 1. Login
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login/access-token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if resp.status_code != 200:
        print(f"Login Failed: {resp.text}")
        return
        
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login OK")
    
    # 2. Ingest
    print("Ingesting dummy data...")
    ingest_payload = {
        "text": "Debug content for RAG analysis. Project status is Green.",
        "metadata": {
            "client_id": "icici_lombard",
            "project_id": "icici_001",
            "filename": "debug.txt"
        }
    }
    r_ing = requests.post(f"{BASE_URL}/api/v1/automation/ingest", json=ingest_payload, headers=headers)
    print(f"Ingest Status: {r_ing.status_code}")
    print(f"Ingest Response: {r_ing.text}")
    
    # 3. Extract
    print("Extracting...")
    extract_payload = {"project_name": "ICICI Lombard Concierge Essential MS-T&M"}
    r_ext = requests.post(f"{BASE_URL}/api/v1/automation/extract", json=extract_payload, headers=headers)
    
    print(f"Extract Status: {r_ext.status_code}")
    print(f"Extract Response: {r_ext.text}")

if __name__ == "__main__":
    debug()
