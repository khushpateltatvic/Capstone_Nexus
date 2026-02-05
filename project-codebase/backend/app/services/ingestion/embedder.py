"""
Embedding Service - Generates vector embeddings for document chunks.

Supports multiple embedding providers:
- HuggingFace (default): Uses sentence-transformers locally
- Gemini: Uses Google's embedding API
"""

import logging
from typing import List, Optional
import time
import asyncio
from app.core.config import settings


class EmbeddingService:
    """Generates vector embeddings for text chunks."""
    
    def __init__(self):
        """Initialize the embedding model based on config."""
        self.provider = settings.EMBEDDING_PROVIDER
        self.model_name = settings.EMBEDDING_MODEL
        self._embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            if self.provider == "gemini":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.GOOGLE_API_KEY
                )
                logging.info("Initialized Gemini embeddings")
            elif self.provider == "ollama":
                from langchain_ollama import OllamaEmbeddings
                self._embeddings = OllamaEmbeddings(
                    model=self.model_name,
                    base_url=settings.OLLAMA_BASE_URL
                )
                logging.info(f"Initialized Ollama embeddings: {self.model_name}")
            else:
                # Default to HuggingFace (Warning: requires torch/transformers)
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    self._embeddings = HuggingFaceEmbeddings(
                        model_name=self.model_name,
                        model_kwargs={"device": "cpu"},
                        encode_kwargs={"normalize_embeddings": True}
                    )
                    logging.info(f"Initialized HuggingFace embeddings: {self.model_name}")
                except ImportError:
                    logging.error("HuggingFaceEmbeddings not available. Please install torch/transformers or use 'gemini'/'ollama'.")
                    raise
        except Exception as e:
            logging.error(f"Failed to initialize embeddings: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return []
        
        # Wrapping sync call in thread
        return await asyncio.to_thread(self._embeddings.embed_query, text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        
        return await asyncio.to_thread(self._embeddings.embed_documents, valid_texts)
    
    async def embed_texts_batched(self, texts: List[str], batch_size: int = 50) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using precise throttling.
        
        Optimized for Gemini Free Tier:
        - RPM: 100
        - TPM: 30,000
        
        Strategy:
        - Batch Size: 50
        - Sleep: 30s between batches
        """
        if not texts:
            return []
        
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
            
        all_embeddings = []
        total_docs = len(valid_texts)
        
        logging.info(f"🚀 Batching {total_docs} docs (30k TPM / 100 RPM Optimized)")
        
        for i in range(0, total_docs, batch_size):
            batch = valid_texts[i : i + batch_size]
            try:
                # Rate limit safety
                if i > 0 and self.provider == "gemini":
                    sleep_time = 20 
                    logging.info(f"⏳ Rate Limit Safety: Sleeping {sleep_time}s... ({i}/{total_docs} complete)")
                    await asyncio.sleep(sleep_time)
                    
                batch_embeddings = await asyncio.to_thread(self._embeddings.embed_documents, batch)
                all_embeddings.extend(batch_embeddings)
                logging.info(f"✅ Embedded batch {i // batch_size + 1}/{(total_docs + batch_size - 1) // batch_size}")
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Handle rate limiting
                if "429" in error_msg or "resource_exhausted" in error_msg:
                    logging.warning("⚠️ Hit Gemini Quota Limit. Cooling down for 60s...")
                    await asyncio.sleep(60)
                    retry_batch = await asyncio.to_thread(self._embeddings.embed_documents, batch)
                    all_embeddings.extend(retry_batch)
                
                # Handle connection reset errors
                elif "connection reset by peer" in error_msg or "errno 104" in error_msg or "connection" in error_msg:
                    logging.warning(f"⚠️ Connection error at batch {i // batch_size + 1}. Retrying in 10s...")
                    await asyncio.sleep(10)
                    
                    # Retry up to 3 times
                    for retry in range(3):
                        try:
                            retry_batch = await asyncio.to_thread(self._embeddings.embed_documents, batch)
                            all_embeddings.extend(retry_batch)
                            logging.info(f"✅ Retry successful for batch {i // batch_size + 1}")
                            break
                        except Exception as retry_e:
                            if retry < 2:
                                logging.warning(f"⚠️ Retry {retry + 1} failed. Waiting 15s...")
                                await asyncio.sleep(15)
                            else:
                                logging.error(f"❌ All retries failed for batch {i // batch_size + 1}: {retry_e}")
                                # Continue with next batch instead of failing completely
                                continue
                
                else:
                    logging.error(f"❌ Batch Failure at index {i}: {e}")
                    # Continue with next batch instead of failing completely
                    continue
                
        return all_embeddings
    
    @property
    def dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        # Most HuggingFace models use 768 or 1024 dimensions
        # BGE-large uses 1024
        if "bge-large" in self.model_name.lower():
            return 1024
        elif "bge-base" in self.model_name.lower():
            return 768
        elif self.provider == "gemini":
            return 768
        else:
            return 768  # Default


# Singleton instance
embedding_service = EmbeddingService()
