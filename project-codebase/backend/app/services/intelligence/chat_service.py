import logging
from typing import List, Dict, Any, Optional
from app.services.ingestion.vector_store import vector_store
from app.services.intelligence.prompts import CHATBOT_TEMPLATE
from langchain_groq import ChatGroq
from app.core.config import settings
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

class ChatService:
    """Service for handling RAG-based chat queries with project context filtering."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.1,
            model_name=settings.GROQ_MODEL_4, # Use a fast model for chat
            groq_api_key=settings.GROQ_API_KEY
        )

    async def chat(self, query: str, client_id: Optional[str] = None, project_id: Optional[str] = None, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Processes a chat query using RAG with project/client filtering.
        1. Query Pinecone for context filtered by project/client.
        2. Format prompt with history and context.
        3. Get response from LLM.
        """
        try:
            # Determine context scope for logging and filtering
            context_scope = "Global"
            if project_id:
                context_scope = f"Project: {project_id}"
            elif client_id:
                context_scope = f"Client: {client_id}"
            
            logging.info(f"Processing chat query [{context_scope}]: {query}")
            
            # 1. Retrieve context from Pinecone with project/client filtering
            chunks = await vector_store.query(
                query_text=query,
                client_id=client_id if not project_id else None,  # Only use client_id if no project_id
                project_id=project_id,
                n_results=10
            )
            
            context_parts = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                source = meta.get("filename", "unknown")
                source_type = meta.get("source", "external")
                chunk_project = meta.get("project_id", "Unknown Project")
                content = chunk.get("content", "")
                
                # Add project context to source information
                source_info = f"{source_type.upper()} | {source}"
                if chunk_project != "Unknown Project":
                    source_info += f" (Project: {chunk_project})"
                
                context_parts.append(f"[{source_info}]\n{content}")
            
            context_str = "\n\n---\n\n".join(context_parts)
            
            # 2. Prepare history
            formatted_history = []
            if history:
                for msg in history:
                    if msg["role"] == "user":
                        formatted_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        formatted_history.append(AIMessage(content=msg["content"]))

            # 3. Add project context to system prompt
            project_context_note = ""
            if project_id:
                project_context_note = f"\n\nIMPORTANT: You are answering in the context of Project ID: {project_id}. Focus your response on information relevant to this specific project only. If information from other projects appears in the context, ignore it unless specifically relevant to {project_id}."
            elif client_id:
                project_context_note = f"\n\nIMPORTANT: You are answering in the context of Client ID: {client_id}. Focus your response on information relevant to this specific client only."

            # 4. Generate response
            # Note: Since CHATBOT_TEMPLATE might not be in prompts.py yet, 
            # we check if it exists or use a fallback.
            try:
                from app.services.intelligence.prompts import CHATBOT_TEMPLATE
            except ImportError:
                # Fallback template if prompts.py update failed
                from langchain_core.prompts import ChatPromptTemplate
                CHATBOT_TEMPLATE = ChatPromptTemplate.from_messages([
                    ("system", "You are the Nexus Assistant. Use the context to answer questions accurately and concisely.\n\nContext:\n{context}{project_context_note}"),
                    ("placeholder", "{history}"),
                    ("user", "{query}")
                ])

            prompt = CHATBOT_TEMPLATE.format_messages(
                context=context_str,
                project_context_note=project_context_note,
                history=formatted_history,
                query=query
            )
            
            response = await self.llm.ainvoke(prompt)
            
            # Extract unique sources with project context
            sources = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                source = meta.get("filename", "unknown")
                chunk_project = meta.get("project_id", "Unknown Project")
                
                source_info = source
                if chunk_project != "Unknown Project":
                    source_info += f" (Project: {chunk_project})"
                sources.append(source_info)
            
            return {
                "response": response.content,
                "sources": list(set(sources)),
                "project_context": context_scope
            }
            
        except Exception as e:
            logging.error(f"Chat error: {e}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request.",
                "sources": [],
                "project_context": context_scope if 'context_scope' in locals() else "Unknown"
            }

chat_service = ChatService()
