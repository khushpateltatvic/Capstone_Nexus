import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from app.services.ingestion.embedder import embedding_service
import asyncio
import time

class PineconeStore:
    """Manages Pinecone vector store operations."""
    
    def __init__(self):
        self.api_key = settings.PINECONE_API_KEY
        self.index_name = settings.PINECONE_INDEX_NAME
        self.environment = "us-east-1" # Default for Starter
        self.pc = None
        self.index = None
        
        self._initialized = False
        
        # We NO LONGER initialize on __init__ to avoid startup hangs
        # if settings.VECTOR_STORE_PROVIDER == "pinecone":
        #     self._initialize()

    def _initialize(self):
        if self._initialized:
            return
        try:
            self.pc = Pinecone(api_key=self.api_key)
            
            # Check if index exists
            existing_indexes = [i.name for i in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                logging.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=embedding_service.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
            
            self.index = self.pc.Index(self.index_name)
            self._initialized = True
            logging.info("Pinecone initialized successfully.")
            
        except Exception as e:
            logging.error(f"Failed to initialize Pinecone: {e}")
            self.index = None
            self._initialized = False

    async def add_chunks(self, chunks: List[Dict], client_id: str, project_id: str) -> int:
        if not self._initialized:
             self._initialize()
             
        if not self.index or not chunks:
            return 0
        
        vectors = []
        texts = [c["content"] for c in chunks]
        embeddings = await embedding_service.embed_texts_batched(texts)
        
        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{client_id}_{project_id}_{chunk['metadata'].get('filename', 'unknown')}_{i}"
            # Pinecone IDs generally ASCII safe
            chunk_id = "".join(x for x in chunk_id if x.isalnum() or x in "-_")
            
            metadata = {
                "client_id": client_id,
                "project_id": project_id,
                "project_name": chunk['metadata'].get("project_name", project_id),
                "filename": str(chunk["metadata"].get("filename", "unknown")),
                "content": chunk["content"], # Storing content in metadata for retrieval
                "source": chunk["metadata"].get("source", "unknown")
            }
            
            vectors.append({
                "id": chunk_id,
                "values": embeddings[i],
                "metadata": metadata
            })
            
        # Batch upsert (Pinecone recommends batches of 100)
        batch_size = 100
        count = 0
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i : i + batch_size]
            try:
                # Upsert is blocking in pinecone-client, we wrap in thread
                await asyncio.to_thread(self.index.upsert, vectors=batch)
                count += len(batch)
            except Exception as e:
                logging.error(f"Pinecone upsert error: {e}")
                
        return count

    async def query(
        self,
        query_text: Any,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        n_results: int = 10,
        extra_filters: Dict[str, Any] = None,
        content_filter_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        
        if not self._initialized:
            self._initialize()

        if not self.index:
            return []
            
        queries = [query_text] if isinstance(query_text, str) else query_text
        all_matches = []
        
        # Build filter
        filter_dict = {}
        if client_id:
            filter_dict["client_id"] = {"$eq": client_id}
        if project_id:
            filter_dict["project_id"] = {"$eq": project_id}
        if extra_filters:
            for k, v in extra_filters.items():
                filter_dict[k] = {"$eq": v}
        
        final_results = []
        
        for q in queries:
            embedding = await embedding_service.embed_text(q)
            if not embedding:
                continue
                
            try:
                # query is blocking, wrap in thread
                results = await asyncio.to_thread(
                    self.index.query,
                    vector=embedding,
                    top_k=n_results * 2,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
                
                for match in results.matches:
                    content = match.metadata.get("content", "")
                    
                    final_results.append({
                        "id": match.id,
                        "content": content,
                        "metadata": match.metadata,
                        "distance": match.score # Pinecone returns similarity score (higher is better)
                    })
            except Exception as e:
                logging.error(f"Pinecone query error: {e}")
                
        final_results.sort(key=lambda x: x["distance"], reverse=True)
        return final_results[:n_results]

pinecone_store = PineconeStore()
