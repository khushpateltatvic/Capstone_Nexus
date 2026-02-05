
import logging
from app.services.ingestion.vector_store import vector_store

logging.basicConfig(level=logging.ERROR)

def check_count():
    if not vector_store._collection:
        print("Collection not initialized.")
        return
    
    count = vector_store._collection.count()
    print(f"Total Chunks in ChromaDB: {count}")
    
    # Sample a few to see size
    sample = vector_store._collection.get(limit=5, include=['metadatas', 'documents'])
    if sample['ids']:
        first_doc_len = len(sample['documents'][0])
        first_meta_keys = list(sample['metadatas'][0].keys())
        print(f"Typical Chunk Text Length: {first_doc_len} characters")
        print(f"Metadata Keys: {first_meta_keys}")

if __name__ == "__main__":
    check_count()
