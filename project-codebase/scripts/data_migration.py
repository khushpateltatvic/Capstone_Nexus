import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load configuration from your backend/.env
load_dotenv("../backend/.env")

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    print("MONGO_URI not found in .env")
    exit(1)

# Initialize MongoDB Connection
client = MongoClient(mongo_uri)
db_name = mongo_uri.split("/")[-1].split("?")[0] or "project_nexus"
db = client[db_name]

print(f"--- STARTING MIGRATION TO: {db_name} ---")

def migrate_excel_to_mongo(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    try:
        # Load the Excel file
        df = pd.read_excel(file_path)
        
        # Required columns based on your request
        # Name, Role, Department, Location, Email, Password
        data_to_insert = df.to_dict(orient='records')

        if data_to_insert:
            # Based on your delete script, it seems 'user_profiles' 
            # is the best fit for user/staff data.
            result = db["user_profiles"].insert_many(data_to_insert)
            print(f"Successfully migrated {len(result.inserted_ids)} records to 'user_profiles'.")
        else:
            print("Excel file is empty.")

    except Exception as e:
        print(f"Migration failed: {e}")

# --- Execute Migration ---
# Ensure your Excel file is named 'data.xlsx' or update the path below
EXCEL_FILE = "data.xlsx" 
migrate_excel_to_mongo(EXCEL_FILE)

print("--- MIGRATION COMPLETE ---")
print("Note: If you need to re-index ChromaDB, run your embedding script next.")