
import logging
import asyncio
import os
import sys

# Add current dir to path to find app
sys.path.append(os.getcwd())

from app.services.ingestion.vector_store import vector_store

logging.basicConfig(level=logging.INFO)

async def diagnose():
    print("--- RAG Diagnostic ---")
    
    # 1. Search for 'RAGQueryService' (Code Hallucination check)
    print("\n[1] Checking for source code in Vector Store...")
    code_results = vector_store.query("RAGQueryService", n_results=5)
    for i, res in enumerate(code_results):
        print(f"\nResult {i+1}:")
        print(f"  Source: {res['metadata'].get('filename', 'Unknown')}")
        print(f"  Project: {res['metadata'].get('project_name', 'None')}")
        print(f"  Snippet: {res['content'][:200]}...")

    # 2. Check for ICICI Lombard overlap
    print("\n[2] Checking for ICICI Lombard cross-project data...")
    # Target a specific project
    target = "ICICI Lombard GA4"
    icici_results = vector_store.query(target, n_results=10)
    
    # Simulate the filter I added to query_service.py
    unique_projects = set()
    for res in icici_results:
        p_name = res['metadata'].get('project_name', 'Untagged')
        unique_projects.add(p_name)
    
    print(f"Projects found matching '{target}': {unique_projects}")
    
    if len([p for p in unique_projects if p != target and p != 'Untagged']) > 0:
        print("⚠️ CONTAMINATION DETECTED: Semantic search retrieved other projects.")
    else:
        print("✅ CLEAN: No conflicting projects in top results.")

    # 3. Test Deep Content Filter
    print("\n[3] Testing Deep Content Filter ($contains)...")
    content_query = "ICICI Lombard"
    deep_results = vector_store.query(
        "irrelevant query text", 
        n_results=5,
        content_filter_str=content_query
    )
    print(f"Deep Search for content '{content_query}' returned {len(deep_results)} chunks.")
    if len(deep_results) > 0:
        print(f"Sample: {deep_results[0]['content'][:100]}...")
    else:
        print("⚠️ Deep Search found nothing. Check ChromaDB version/support.")
