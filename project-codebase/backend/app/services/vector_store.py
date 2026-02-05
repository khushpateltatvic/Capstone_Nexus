import chromadb
from chromadb.config import Settings
from app.core.config import settings
from typing import List, Dict, Any, Optional

class VectorStore:
    def __init__(self):
        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="account_intelligence",
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]):
        """
        Add documents to the vector store.
        """
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query_text: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None):
        """
        Query the vector store.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where
        )
        return results

# Singleton instance
vector_store = VectorStore()
