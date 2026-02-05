import os
import logging
from pinecone import Pinecone
from app.core.config import settings
from app.services.ingestion.embedder import embedding_service
from groq import Groq
from typing import Optional

# Load keys from environment
# We use settings from config to ensure we use the loaded values
PINECONE_API_KEY = settings.PINECONE_API_KEY
PINECONE_INDEX_NAME = settings.PINECONE_INDEX_NAME

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
try:
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    logging.error(f"Failed to connect to Pinecone index: {e}")
    index = None

# Initialize LLM Client (using Groq as drop-in replacement for OpenAI)
client = Groq(api_key=settings.GROQ_API_KEY)

async def get_nexus_answer(query: str, client_id: Optional[str] = None, project_id: Optional[str] = None):
    if not index:
        return {"answer": "Vector store not initialized.", "sources": [], "project_context": None}

    # Determine context scope for logging
    context_scope = "Global"
    if project_id:
        context_scope = f"Project: {project_id}"
    elif client_id:
        context_scope = f"Client: {client_id}"
    
    logging.info(f"Querying Nexus Chatbot [{context_scope}]: {query}")
    
    # 1. Embed the user query
    try:
        query_vector = await embedding_service.embed_text(query)
        logging.info(f"Embedding generated. Type: {type(query_vector)}, Length: {len(query_vector) if query_vector else 0}")
    except Exception as e:
        logging.error(f"Embedding generation failed: {e}")
        return {"answer": "Error generating embedding.", "sources": [], "project_context": context_scope}
    
    if not query_vector:
        return {"answer": "Could not generate embedding for query.", "sources": [], "project_context": context_scope}

    # 2. Build Pinecone filter based on project/client context
    pinecone_filter = {}
    
    if project_id:
        # Filter to specific project only
        pinecone_filter["project_id"] = project_id
        logging.info(f"Filtering chat results to project: {project_id}")
    elif client_id:
        # Filter to specific client (all projects under that client)
        pinecone_filter["client_id"] = client_id
        logging.info(f"Filtering chat results to client: {client_id}")
    else:
        # No filter - search all content (global chat)
        logging.info("No project/client filter - searching all content")

    # 3. Query Pinecone for context with filters
    try:
        logging.info(f"Querying Pinecone index {PINECONE_INDEX_NAME} with filter: {pinecone_filter}")
        
        query_params = {
            "vector": query_vector,
            "top_k": 5, 
            "include_metadata": True
        }
        
        # Only add filter if we have one
        if pinecone_filter:
            query_params["filter"] = pinecone_filter
            
        search_results = index.query(**query_params)
        logging.info(f"Pinecone results type: {type(search_results)}")
        logging.info(f"Pinecone results: {search_results}")
    except Exception as e:
        logging.error(f"Pinecone query failed: {e}")
        return {"answer": "Error querying knowledge base.", "sources": [], "project_context": context_scope}

    # 4. Construct Context from results
    context_text = ""
    sources = []
    
    if search_results and hasattr(search_results, 'matches'):
        matches = search_results.matches
    elif search_results and isinstance(search_results, dict) and 'matches' in search_results:
        matches = search_results['matches']
    else:
        logging.warning("No matches found or invalid structure.")
        matches = []

    for match in matches:
        # Threshold: 0.3 is a reasonable starting point for cosine similarity
        current_score = getattr(match, 'score', match.get('score', 0))
        if current_score > 0.3: 
            metadata = getattr(match, 'metadata', match.get('metadata', {}))
            
            # Handle 'content' vs 'text' key difference
            content = metadata.get('content', metadata.get('text', ''))
            source_name = metadata.get('filename', metadata.get('source', 'Unknown'))
            source_project = metadata.get('project_id', 'Unknown Project')
            
            # Add project context to source information
            source_info = f"{source_name}"
            if source_project != 'Unknown Project':
                source_info += f" (Project: {source_project})"
            
            context_text += f"[Source: {source_info}]\n{content}\n---\n"
            sources.append(source_info)

    logging.info(f"Context constructed. Sources: {sources}")

    # 5. Generate Answer with LLM - Include project context in prompt
    project_context_note = ""
    if project_id:
        project_context_note = f"\n\nIMPORTANT: You are answering in the context of Project ID: {project_id}. Focus your response on information relevant to this specific project."
    elif client_id:
        project_context_note = f"\n\nIMPORTANT: You are answering in the context of Client ID: {client_id}. Focus your response on information relevant to this specific client."

    system_prompt = f"""You are the Nexus AI Assistant. Use the following context to answer the user's question. 
    If the answer is not in the context, say you don't know.
    
    Context:
    {context_text}{project_context_note}
    """

    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL_4, # Using Llama3-8b-instant for speed
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        
        answer = completion.choices[0].message.content
    except Exception as e:
        logging.error(f"LLM generation failed: {e}")
        answer = "I'm sorry, I encountered an error generating the response."

    return {
        "answer": answer,
        "sources": list(set(sources)),
        "project_context": context_scope
    }
