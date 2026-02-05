
import asyncio
from app.services.ingestion.vector_store import vector_store

async def debug_chroma():
    # project_id from previous check: 14694380
    client_id = "basecamp"
    project_id = "14694380"
    
    chunks = vector_store.get_all_for_project(client_id, project_id)
    print(f"\nFound {len(chunks)} chunks in ChromaDB for {client_id}/{project_id}")
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} ---")
        print(f"Content: {chunk['content'][:500]}...") # First 500 chars
        print(f"Metadata: {chunk['metadata']}")

if __name__ == "__main__":
    asyncio.run(debug_chroma())
