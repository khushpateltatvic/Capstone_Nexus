#!/usr/bin/env python3
"""
Test querying Pinecone to see if Basecamp documents were stored
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
        logger.info("Testing Pinecone queries for Basecamp data...")
        
        from app.services.ingestion.pinecone_store import pinecone_store
        from app.services.ingestion.vector_store import vector_store
        
        # Initialize Pinecone
        if not pinecone_store._initialized:
            pinecone_store._initialize()
        
        if not pinecone_store.index:
            logger.error("❌ Pinecone not available")
            return
        
        logger.info(f"✅ Connected to Pinecone index: {pinecone_store.index_name}")
        
        # Test queries for Basecamp content
        test_queries = [
            "ICICI Lombard",
            "marketing",
            "concierge",
            "GA4",
            "consulting",
            "todos",
            "project management"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Searching for: '{query}'")
            
            # Query using vector store (which should use Pinecone)
            results = await vector_store.query(
                query_text=query,
                client_id="basecamp",
                n_results=5
            )
            
            logger.info(f"📊 Found {len(results)} results")
            
            for i, result in enumerate(results):
                content_preview = result['content'][:100].replace('\n', ' ')
                metadata = result.get('metadata', {})
                project_name = metadata.get('project_name', 'Unknown')
                filename = metadata.get('filename', 'Unknown')
                
                logger.info(f"   {i+1}. {project_name}")
                logger.info(f"      File: {filename}")
                logger.info(f"      Content: {content_preview}...")
                logger.info(f"      Score: {result.get('distance', 0):.4f}")
        
        # Also test direct Pinecone query
        logger.info(f"\n🔍 Direct Pinecone query for 'ICICI'")
        direct_results = await pinecone_store.query(
            query_text="ICICI",
            client_id="basecamp",
            n_results=3
        )
        
        logger.info(f"📊 Direct Pinecone results: {len(direct_results)}")
        for i, result in enumerate(direct_results):
            content_preview = result['content'][:100].replace('\n', ' ')
            logger.info(f"   {i+1}. {content_preview}... (score: {result.get('distance', 0):.4f})")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())