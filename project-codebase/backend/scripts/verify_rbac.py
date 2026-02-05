import requests
import sys
import uuid

BASE_URL = "http://localhost:8000/api/v1"

def get_token(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login/access-token", data={
        "username": email,
        "password": password
    })
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None

def register_user(email, password):
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
        "role": "analyst" # Non-admin
    }, headers={"X-Admin-Secret": "supersecretkey"}) # Assuming default dev key, or we skip if this fails
    return resp

def test_rbac():
    print("=======================================")
    print("      RBAC VERIFICATION SUITE")
    print("=======================================")
    
    # 1. Admin Test (ravi@tatvic.com)
    print("\n[Step 1] Testing Admin Access (ravi@tatvic.com)...")
    admin_token = get_token("ravi@tatvic.com", "Admin@123")
    
    if admin_token:
        print("✅ Admin Login Successful")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Admin should access /auth/users
        resp = requests.get(f"{BASE_URL}/auth/users", headers=headers)
        if resp.status_code == 200:
            print("✅ Admin Access to /auth/users: ALLOWED (Expected)")
        else:
            print(f"❌ Admin Access to /auth/users: FAILED ({resp.status_code})")
            
        # Check Basecamp endpoint
        resp_bc = requests.get(f"{BASE_URL}/automation/basecamp/projects", headers=headers)
        if resp_bc.status_code == 200:
            print("✅ Admin Access to Basecamp Projects: ALLOWED")
        else:
            print(f"❌ Admin Access to Basecamp Projects: FAILED ({resp_bc.status_code})")
            
    else:
        print("❌ Admin Login Failed (Credentials might be wrong)")

    # 2. Standard User Test
    print("\n[Step 2] Testing Standard User Access...")
    user_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    user_pass = "User@123"
    
    # Register/Login
    print(f"Creating limited user: {user_email}")
    # Try register with secret (assuming DEV secret is 'supersecretkey' or similar from settings)
    # If not known, we might fail here. Let's try to assume we can register.
    # Actually, main.py imports config. settings.SECRET_KEY is needed.
    # Let's try registering without secret if endpoint allows (unlikely) or use a known dev secret.
    # If register fails 403, we skip this part or fail.
    
    # To resolve this, I will try to read settings or just try a likely secret.
    # Or, simpler: Just use the 'admin' token to CREATE a user if an endpoint exists? 
    # The register endpoint requires header.
    
    # Let's look at auth.py again... 
    # @router.post("/register") requires x_admin_secret.
    
    # If I can't register, I can't test non-admin cleanly unless I know the secret.
    # The secret is loaded from env.
    
    # WORKAROUND: I will try to use the 'admin_token' to hit endpoints, but... that proves admin works.
    # Validating 403 requires a non-admin.
    
    # Let's try to register with a dummy secret. If it fails, we report "Cannot create non-admin user".
    
    reg_resp = register_user(user_email, user_pass)
    user_token = None
    
    if reg_resp.status_code == 200:
        print("✅ User Registration Successful")
        user_token = get_token(user_email, user_pass)
    elif reg_resp.status_code == 403:
         print("⚠️ Registration Forbidden (Secret Key mismatch). Skipping Non-Admin test.")
    else:
         print(f"❌ Registration Failed: {reg_resp.text}")

    if user_token:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Non-Admin should FAIL /auth/users
        print("Attempting to access Admin Endpoint as Standard User...")
        resp = requests.get(f"{BASE_URL}/auth/users", headers=headers)
        
        if resp.status_code == 403:
            print("✅ RBAC ENFORCED: Standard User Blocked (403) from /auth/users")
        else:
             print(f"❌ SECURITY FAILURE: Standard User Accessed Admin Endpoint ({resp.status_code})")
             
        # Non-Admin should ACCESS Basecamp? (Assuming 'auth users' generally can)
        resp_bc = requests.get(f"{BASE_URL}/automation/basecamp/projects", headers=headers)
        if resp_bc.status_code == 200:
             print("✅ Standard User Access to Basecamp: ALLOWED")
        elif resp_bc.status_code == 403:
             print("ℹ️ Standard User Access to Basecamp: DENIED (Maybe intended)")
        else:
             print(f"❌ Standard User Basecamp Check Failed ({resp_bc.status_code})")

    print("\n---------------------------------------")

if __name__ == "__main__":
    test_rbac()
