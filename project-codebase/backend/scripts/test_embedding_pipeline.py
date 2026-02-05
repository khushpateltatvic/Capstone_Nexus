#!/usr/bin/env python3
"""
Test script to verify the embedding pipeline from Basecamp to Pinecone
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.ingestion.embedder import embedding_service
from app.services.ingestion.pinecone_store import pinecone_store
from app.services.ingestion.basecamp import basecamp_service
from app.core.database import db

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_embedding_service():
    """Test the Gemini embedding service"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING GEMINI EMBEDDING SERVICE")
    logger.info("=" * 60)
    
    try:
        # Test single embedding
        test_text = "This is a test document for embedding generation."
        logger.info(f"📝 Test text: {test_text}")
        
        embedding = await embedding_service.embed_text(test_text)
        logger.info(f"✅ Single embedding generated: {len(embedding)} dimensions")
        logger.info(f"📊 First 5 values: {embedding[:5]}")
        
        # Test batch embedding
        test_texts = [
            "First test document about project management",
            "Second test document about technical implementation", 
            "Third test document about marketing strategy"
        ]
        
        logger.info(f"📝 Testing batch embedding with {len(test_texts)} texts")
        batch_embeddings = await embedding_service.embed_texts_batched(test_texts)
        logger.info(f"✅ Batch embeddings generated: {len(batch_embeddings)} embeddings")
        
        for i, emb in enumerate(batch_embeddings):
            logger.info(f"   📊 Embedding {i+1}: {len(emb)} dimensions")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Embedding service test failed: {e}")
        return False

async def test_pinecone_connection():
    """Test Pinecone connection and operations"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING PINECONE CONNECTION")
    logger.info("=" * 60)
    
    try:
        # Initialize Pinecone
        if not pinecone_store._initialized:
            logger.info("🔧 Initializing Pinecone...")
            pinecone_store._initialize()
        
        if not pinecone_store.index:
            logger.error("❌ Pinecone index not available")
            return False
            
        logger.info(f"✅ Pinecone index '{pinecone_store.index_name}' is available")
        
        # Test adding chunks
        test_chunks = [
            {
                "content": "This is a test chunk for Pinecone storage",
                "metadata": {
                    "filename": "test_doc.txt",
                    "project_name": "Test Project",
                    "source": "test"
                }
            }
        ]
        
        logger.info("📤 Testing chunk upload to Pinecone...")
        count = await pinecone_store.add_chunks(test_chunks, "test_client", "test_project")
        logger.info(f"✅ Added {count} chunks to Pinecone")
        
        # Test querying
        logger.info("🔍 Testing Pinecone query...")
        results = await pinecone_store.query("test chunk", "test_client", "test_project", n_results=5)
        logger.info(f"✅ Query returned {len(results)} results")
        
        for i, result in enumerate(results):
            logger.info(f"   📄 Result {i+1}: {result['content'][:50]}... (score: {result['distance']:.4f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinecone test failed: {e}")
        return False

async def test_basecamp_sync():
    """Test Basecamp sync and document processing"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING BASECAMP SYNC")
    logger.info("=" * 60)
    
    try:
        # Connect to database
        await db.connect()
        
        # Check Basecamp configuration
        logger.info(f"🔧 Basecamp enabled: {settings.ENABLE_BASECAMP}")
        logger.info(f"🔧 Basecamp service enabled: {basecamp_service.enabled}")
        logger.info(f"📋 Project IDs: {basecamp_service.project_ids}")
        
        if not basecamp_service.enabled:
            logger.warning("⚠️ Basecamp service is not enabled")
            return False
        
        # Check sync status for each project
        for project_id in basecamp_service.project_ids:
            last_sync = await basecamp_service.get_last_sync_time(project_id)
            logger.info(f"📋 Project {project_id}: Last sync = {last_sync}")
        
        # Test sync for one project (don't sync all to avoid rate limits)
        test_project_id = basecamp_service.project_ids[0]
        logger.info(f"🚀 Testing sync for project {test_project_id}")
        
        # This would normally trigger a full sync, but let's just check the API connection
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                project_url = f"{basecamp_service.base_url}/{basecamp_service.account_id}/projects/{test_project_id}.json"
                response = await client.get(project_url, headers=basecamp_service.headers)
                
                if response.status_code == 200:
                    project_data = response.json()
                    logger.info(f"✅ Basecamp API connection successful")
                    logger.info(f"📋 Project name: {project_data.get('name', 'Unknown')}")
                    return True
                else:
                    logger.error(f"❌ Basecamp API error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Basecamp API test failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Basecamp sync test failed: {e}")
        return False
    finally:
        await db.close()

async def test_full_pipeline():
    """Test the complete pipeline from Basecamp to Pinecone"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING COMPLETE PIPELINE")
    logger.info("=" * 60)
    
    try:
        # Simulate a document from Basecamp
        test_document = {
            "filename": "basecamp_test.txt",
            "content": b"This is a test document from Basecamp containing project information about marketing strategies and technical implementation details.",
            "client_id": "basecamp",
            "project_id": "test_project",
            "project_name": "Test Marketing Project",
            "source": "basecamp"
        }
        
        logger.info("📄 Simulating document processing...")
        
        # Process through the chunker
        from app.services.ingestion.chunker import chunker
        
        text_content = test_document["content"].decode('utf-8')
        metadata = {
            "client_id": test_document["client_id"],
            "project_id": test_document["project_id"],
            "filename": test_document["filename"],
            "source": test_document["source"],
            "project_name": test_document["project_name"]
        }
        
        chunks = chunker.chunk_document(text=text_content, metadata=metadata)
        logger.info(f"✅ Created {len(chunks)} chunks")
        
        # Add to vector store (which should use Pinecone)
        from app.services.ingestion.vector_store import vector_store
        
        count = await vector_store.add_chunks(
            chunks=chunks,
            client_id=test_document["client_id"],
            project_id=test_document["project_id"]
        )
        logger.info(f"✅ Added {count} chunks to vector store")
        
        # Test querying
        results = await vector_store.query(
            query_text="marketing strategies",
            client_id=test_document["client_id"],
            project_id=test_document["project_id"],
            n_results=3
        )
        logger.info(f"✅ Query returned {len(results)} results")
        
        for i, result in enumerate(results):
            logger.info(f"   📄 Result {i+1}: {result['content'][:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full pipeline test failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 STARTING EMBEDDING PIPELINE TESTS")
    logger.info("=" * 80)
    
    tests = [
        ("Embedding Service", test_embedding_service),
        ("Pinecone Connection", test_pinecone_connection),
        ("Basecamp Sync", test_basecamp_sync),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"📊 {test_name}: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"📊 {test_name}: ❌ FAILED with exception: {e}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The embedding pipeline is working correctly.")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())