from pymongo import MongoClient
import os
import shutil
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv("../backend/.env")

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("MONGO_URI not found in .env")
    exit(1)

client = MongoClient(mongo_uri)
db_name = mongo_uri.split("/")[-1].split("?")[0] or "project_nexus"
db = client[db_name]

print(f"Connecting to MongoDB: {db_name}")

# Clear MongoDB Collections
collections = ["client_profiles", "risk_registers", "stakeholder_maps", "case_studies", "master_docs"]
for c in collections:
    res = db[c].delete_many({})
    print(f"Cleared collection '{c}': Deleted {res.deleted_count} docs.")

# Clear ChromaDB Directory
chroma_path = "backend/chroma_db"
if os.path.exists(chroma_path):
    shutil.rmtree(chroma_path)
    print(f"Deleted ChromaDB directory: {chroma_path}")
else:
    print(f"ChromaDB directory not found at {chroma_path}")

print("--- FULL RESET COMPLETE ---")
