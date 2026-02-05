"""
Ingestion Service - Handles document chunking, embedding, and vector storage.

Pipeline:
1. Chunker: Splits documents into semantic chunks
2. Embedder: Generates vector embeddings using HuggingFace/Gemini
3. VectorStore: Stores embeddings in ChromaDB with metadata
"""

from .chunker import DocumentChunker
from .embedder import EmbeddingService
from .vector_store import VectorStoreService

__all__ = ["DocumentChunker", "EmbeddingService", "VectorStoreService"]
