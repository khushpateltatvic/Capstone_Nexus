#!/usr/bin/env python3
"""
Simple test to check embedding and Pinecone integration
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("Testing imports...")
        
        from app.core.config import settings
        logger.info(f"✅ Config loaded - Embedding provider: {settings.EMBEDDING_PROVIDER}")
        logger.info(f"✅ Vector store provider: {settings.VECTOR_STORE_PROVIDER}")
        
        from app.services.ingestion.embedder import embedding_service
        logger.info("✅ Embedding service imported")
        
        # Test embedding
        logger.info("Testing embedding generation...")
        test_text = "This is a test document"
        embedding = await embedding_service.embed_text(test_text)
        logger.info(f"✅ Embedding generated: {len(embedding)} dimensions")
        
        # Test Pinecone
        logger.info("Testing Pinecone...")
        from app.services.ingestion.pinecone_store import pinecone_store
        
        if not pinecone_store._initialized:
            logger.info("Initializing Pinecone...")
            pinecone_store._initialize()
        
        if pinecone_store.index:
            logger.info(f"✅ Pinecone connected to index: {pinecone_store.index_name}")
            
            # Test adding a chunk
            test_chunks = [{
                "content": "Test content for Pinecone",
                "metadata": {
                    "filename": "test.txt",
                    "project_name": "Test Project",
                    "source": "test"
                }
            }]
            
            count = await pinecone_store.add_chunks(test_chunks, "test_client", "test_project")
            logger.info(f"✅ Added {count} chunks to Pinecone")
            
        else:
            logger.error("❌ Pinecone index not available")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())