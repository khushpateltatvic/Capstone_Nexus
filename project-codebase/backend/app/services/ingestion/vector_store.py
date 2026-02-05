"""
Vector Store Service - Manages ChromaDB operations for document storage and retrieval.

Handles:
- Storing document chunks with embeddings
- Querying for relevant chunks based on semantic similarity
- Filtering by metadata (client_id, project_id, etc.)
"""

import logging
from typing import List, Dict, Any, Optional, Union
from .embedder import embedding_service
from app.core.config import settings

# Lazy import to avoid circular or early-init issues if not used
try:
    from app.services.ingestion.pinecone_store import pinecone_store
except ImportError:
    pinecone_store = None


class VectorStoreService:
    """Manages ChromaDB vector store operations."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize Vector Store.
        """
        self.provider = settings.VECTOR_STORE_PROVIDER
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        
        if self.provider == "chroma":
            self._initialize_client()
        elif self.provider == "pinecone":
            logging.info("Vector Store Provider: Pinecone (Cloud)")
    
    def _initialize_client(self):
        """Initialize ChromaDB client with persistence."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create the main collection
            self._collection = self._client.get_or_create_collection(
                name="project_nexus_docs",
                metadata={"description": "Project Nexus document chunks"}
            )
            
            logging.info(f"ChromaDB initialized at {self.persist_directory}")
            logging.info(f"Collection has {self._collection.count()} documents")
            
        except Exception as e:
            logging.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        client_id: str,
        project_id: str
    ) -> int:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of chunk dicts with 'content' and 'metadata'
            client_id: Client identifier for filtering
            project_id: Project identifier for filtering
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
            
        if self.provider == "pinecone" and pinecone_store:
            return await pinecone_store.add_chunks(chunks, client_id, project_id)
            
        if not self._collection:
            return 0
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        # Generate embeddings for all chunks (Batched for Rate Limit Safety)
        texts = [c["content"] for c in chunks]
        chunk_embeddings = await embedding_service.embed_texts_batched(texts)
        
        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{client_id}_{project_id}_{chunk['metadata'].get('filename', 'unknown')}_{i}"
            
            # Prepare metadata (ChromaDB only accepts strings, ints, floats, bools)
            metadata = {
                "client_id": client_id,
                "project_id": project_id,
                "filename": str(chunk["metadata"].get("filename", "unknown")),
                "chunk_index": int(chunk["metadata"].get("chunk_index", 0)),
                "total_chunks": int(chunk["metadata"].get("total_chunks", 1)),
            }
            
            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append(metadata)
            embeddings.append(chunk_embeddings[i])
        
        # Upsert to ChromaDB (handles duplicates)
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        logging.info(f"Added {len(chunks)} chunks for {client_id}/{project_id}")
        return len(chunks)
    
    from typing import Union

    async def query(
        self,
        query_text: Union[str, List[str]],
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        n_results: int = 10,
        extra_filters: Dict[str, Any] = None,
        content_filter_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for relevant chunks with flexible filtering.
        
        Args:
            query_text: Text or list of texts to search for
            client_id: Optional client filter
            project_id: Optional project filter
            n_results: Max results per query string
            extra_filters: Optional additional metadata filters
            content_filter_str: Optional string to match in document content ($contains)
            
        Returns:
            List of unique chunks sorted by distance
        """
        if self.provider == "pinecone" and pinecone_store:
            return await pinecone_store.query(
                query_text, 
                client_id, 
                project_id, 
                n_results, 
                extra_filters, 
                content_filter_str
            )

        if not self._collection:
            return []
            
        # 1. Build dynamic 'where' filter
        filters = []
        if client_id:
            filters.append({"client_id": {"$eq": client_id}})
        if project_id:
            filters.append({"project_id": {"$eq": project_id}})
        if extra_filters:
            for k, v in extra_filters.items():
                filters.append({k: {"$eq": v}})
                
        where_filter = None
        if len(filters) == 1:
            where_filter = filters[0]
        elif len(filters) > 1:
            where_filter = {"$and": filters}

        # 1.5 Build 'where_document' content filter
        where_doc = None
        if content_filter_str:
            where_doc = {"$contains": content_filter_str}

        # 2. Execute search
        queries = [query_text] if isinstance(query_text, str) else query_text
        all_chunks = []
        seen_ids = set()

        for q in queries:
            try:
                # Generate embedding
                query_embedding = await embedding_service.embed_text(q)
                
                # Query ChromaDB
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where_filter,
                    where_document=where_doc,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Process results
                if results and results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        chunk_id = results["ids"][0][i]
                        if chunk_id not in seen_ids:
                            seen_ids.add(chunk_id)
                            all_chunks.append({
                                "content": doc,
                                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                                "distance": results["distances"][0][i] if results["distances"] else 0
                            })
            except Exception as e:
                logging.error(f"Search failed for query '{q}': {e}")
                continue
        
        # 3. Final Sort & Limit
        all_chunks.sort(key=lambda x: x.get("distance", 0))
        return all_chunks[:n_results * 2]
    
    async def get_all_for_project(
        self,
        client_id: str,
        project_id: str
    ) -> List[Dict[str, Any]]:
        """Get all chunks for a specific project."""
        where_filter = {
            "$and": [
                {"client_id": {"$eq": client_id}},
                {"project_id": {"$eq": project_id}}
            ]
        }
        
        results = self._collection.get(
            where=where_filter,
            include=["documents", "metadatas"]
        )
        
        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"]):
                chunks.append({
                    "content": doc,
                    "metadata": results["metadatas"][i] if results["metadatas"] else {}
                })
        
        return chunks
    
    async def delete_project(self, client_id: str, project_id: str) -> int:
        """Delete all chunks for a project."""
        where_filter = {
            "$and": [
                {"client_id": {"$eq": client_id}},
                {"project_id": {"$eq": project_id}}
            ]
        }
        
        # Get IDs to delete
        results = self._collection.get(where=where_filter)
        if results and results["ids"]:
            self._collection.delete(ids=results["ids"])
            logging.info(f"Deleted {len(results['ids'])} chunks for {client_id}/{project_id}")
            return len(results["ids"])
        
        return 0
    
    def clear_all(self):
        """Clear all data from the vector store."""
        self._client.delete_collection("project_nexus_docs")
        self._collection = self._client.get_or_create_collection(
            name="project_nexus_docs",
            metadata={"description": "Project Nexus document chunks"}
        )
        logging.info("Cleared all vector store data")


# Singleton instance
vector_store = VectorStoreService()
