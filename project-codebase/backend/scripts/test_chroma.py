import chromadb
try:
    print("Testing PersistentClient without settings...")
    client = chromadb.PersistentClient(path="./test_db")
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")

try:
    print("\nTesting PersistentClient with minimal settings...")
    from chromadb.config import Settings
    client = chromadb.PersistentClient(
        path="./test_db", 
        settings=Settings(anonymized_telemetry=False)
    )
    print("Success!")
except Exception as e:
    print(f"Failed: {e}")
