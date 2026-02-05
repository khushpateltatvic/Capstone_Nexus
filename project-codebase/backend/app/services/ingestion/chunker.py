"""
Document Chunker - Splits documents into semantic chunks for embedding.

Uses LangChain's RecursiveCharacterTextSplitter for intelligent chunking
that respects sentence and paragraph boundaries.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:
    """Chunks documents into smaller pieces suitable for embedding."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
            separators: List of separators to split on (in order of priority)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len
        )
    
    def chunk_document(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Split a document into chunks with metadata.
        
        Args:
            text: The document text to chunk
            metadata: Metadata to attach to each chunk (client_id, project_id, filename, etc.)
            
        Returns:
            List of chunk dictionaries with 'content' and 'metadata' keys
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        
        # Split into chunks
        chunks = self.splitter.split_text(text)
        
        # Create chunk objects with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk_text)
            }
            
            # Inject metadata context into content for better differentiation
            context_header = ""
            if metadata:
                # Prioritize valid identifying fields
                if "project_name" in metadata:
                    context_header += f"Project: {metadata['project_name']}\n"
                if "client_id" in metadata:
                    context_header += f"Client: {metadata['client_id']}\n"
                if "source" in metadata:
                    context_header += f"Source: {metadata['source']}\n"
                
                # Add basecamp specific IDs if present
                if "project_id" in metadata and metadata.get("source") == "basecamp":
                    context_header += f"ID: {metadata['project_id']}\n"

            # Combine header with content
            final_content = f"{context_header}\n{chunk_text}" if context_header else chunk_text

            result.append({
                "content": final_content,
                "metadata": chunk_metadata
            })
        
        return result
    
    def chunk_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk multiple documents.
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
            
        Returns:
            Flat list of all chunks from all documents
        """
        all_chunks = []
        
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            chunks = self.chunk_document(text, metadata)
            all_chunks.extend(chunks)
        
        return all_chunks


# Singleton instance
chunker = DocumentChunker()
