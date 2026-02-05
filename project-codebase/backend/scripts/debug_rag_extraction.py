#!/usr/bin/env python3
"""
Debug RAG Extraction - Test the multi-source query process
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_queries():
    try:
        logger.info("Testing RAG query process...")
        
        from app.services.rag.query_service import rag_service
        from app.services.ingestion.vector_store import vector_store
        from app.core.database import db
        
        # Connect to database
        await db.connect()
        
        # Test project details
        test_project = {
            "client_id": "icici_lombard",
            "project_id": "icici_41106708", 
            "project_name": "[ICICI Lombard] [Marketing Concierge Essential] [MS - T & M]"
        }
        
        logger.info(f"Testing extraction for: {test_project['project_name']}")
        
        # Test 1: Direct vector store query
        logger.info("\n=== TEST 1: Direct Vector Store Query ===")
        try:
            results = await vector_store.query(
                query_text="ICICI Lombard Marketing Concierge",
                n_results=10
            )
            logger.info(f"Direct query returned {len(results)} results")
            
            for i, result in enumerate(results[:3]):
                content_preview = result['content'][:200].replace('\n', ' ')
                metadata = result.get('metadata', {})
                logger.info(f"  {i+1}. Source: {metadata.get('source', 'unknown')}")
                logger.info(f"     File: {metadata.get('filename', 'unknown')}")
                logger.info(f"     Project: {metadata.get('project_name', 'N/A')}")
                logger.info(f"     Content: {content_preview}...")
                logger.info(f"     Score: {result.get('distance', 0):.4f}")
        except Exception as e:
            logger.error(f"Direct query failed: {e}")
        
        # Test 2: Query with client_id filter
        logger.info("\n=== TEST 2: Query with Basecamp Filter ===")
        try:
            results = await vector_store.query(
                query_text="ICICI Lombard Marketing",
                client_id="basecamp",
                n_results=10
            )
            logger.info(f"Basecamp filtered query returned {len(results)} results")
            
            for i, result in enumerate(results[:3]):
                content_preview = result['content'][:200].replace('\n', ' ')
                metadata = result.get('metadata', {})
                logger.info(f"  {i+1}. Source: {metadata.get('source', 'unknown')}")
                logger.info(f"     File: {metadata.get('filename', 'unknown')}")
                logger.info(f"     Project: {metadata.get('project_name', 'N/A')}")
                logger.info(f"     Content: {content_preview}...")
        except Exception as e:
            logger.error(f"Basecamp filtered query failed: {e}")
        
        # Test 3: Test RAG service context retrieval
        logger.info("\n=== TEST 3: RAG Service Context Retrieval ===")
        try:
            context = await rag_service.retrieve_context(
                section="universal_context",
                client_id=test_project["client_id"],
                project_id=test_project["project_id"],
                project_name=test_project["project_name"],
                n_results=10
            )
            logger.info(f"RAG context length: {len(context)} characters")
            if context:
                logger.info(f"Context preview: {context[:500]}...")
            else:
                logger.warning("No context retrieved!")
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {e}")
        
        # Test 4: Test with different project name variations
        logger.info("\n=== TEST 4: Project Name Variations ===")
        variations = [
            "ICICI Lombard Marketing Concierge Essential",
            "Marketing Concierge Essential",
            "ICICI Lombard",
            "Concierge Essential",
            "Marketing"
        ]
        
        for variation in variations:
            try:
                results = await vector_store.query(
                    query_text=variation,
                    n_results=5
                )
                logger.info(f"'{variation}' -> {len(results)} results")
            except Exception as e:
                logger.error(f"Variation query '{variation}' failed: {e}")
        
        # Test 5: Check what's actually in Pinecone
        logger.info("\n=== TEST 5: Sample Pinecone Content ===")
        try:
            # Query for any content
            results = await vector_store.query(
                query_text="project",
                n_results=5
            )
            logger.info(f"General 'project' query returned {len(results)} results")
            
            for i, result in enumerate(results):
                metadata = result.get('metadata', {})
                logger.info(f"  {i+1}. Client: {metadata.get('client_id', 'N/A')}")
                logger.info(f"     Project: {metadata.get('project_id', 'N/A')}")
                logger.info(f"     Name: {metadata.get('project_name', 'N/A')}")
                logger.info(f"     Source: {metadata.get('source', 'N/A')}")
                logger.info(f"     File: {metadata.get('filename', 'N/A')}")
        except Exception as e:
            logger.error(f"General query failed: {e}")
        
        await db.close()
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_queries())