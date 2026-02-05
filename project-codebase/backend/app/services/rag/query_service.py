"""
RAG Query Service - Retrieves relevant chunks for each section and runs extraction.

This service:
1. Defines section-specific queries
2. Retrieves relevant chunks from ChromaDB
3. Calls specialized agents with the retrieved context
4. Returns structured extraction results
"""

import logging
from typing import Dict, Any, List
from app.services.ingestion.vector_store import vector_store
from app.services.intelligence.agents.historian import HistorianAgent
from app.services.intelligence.agents.pm import PMAgent
from app.services.intelligence.agents.auditor import AuditorAgent
from app.services.intelligence.agents.tech_lead import TechLeadAgent
from app.services.intelligence.agents.strategist import StrategistAgent


# Section-specific queries for RAG retrieval
SECTION_QUERIES = {
    "universal_context": [
        "account summary background client overview company profile",
        "timeline milestones key dates engagement history",
        "engagement type FTE concierge retainer contract model",
        "team members squad contacts who is working",
        "POC contacts stakeholders decision makers",
        "communication email meeting response time frequency"
    ],
    "operations": [
        "project status traffic light health score risk blockers",
        "tasks deadlines upcoming ongoing deliverables sprint",
        "blockers issues problems waiting blocked",
        "meetings interactions calls discussions recent"
    ],
    "technical": [
        "tech stack technology framework database infrastructure tools",
        "access credentials login URL environment staging production",
        "implementation completed deployed released launched",
        "experiments AB test results performance metrics"
    ],
    "commercial": [
        "SOW contract statement of work agreement terms value",
        "financial billing invoice payment budget revenue",
        "renewal contract extension upcoming dates",
        "revenue channels breakdown percentage"
    ],
    "strategy": [
        "stakeholder influence decision maker champion supporter",
        "goals objectives KPIs success metrics roadmap",
        "upsell opportunity expansion additional services",
        "competitors competition landscape alternative"
    ],
    "marketing": [
        "brand colors logo guidelines typography design",
        "success stories case studies wins achievements",
        "testimonials quotes reviews feedback praise",
        "references blog press webinar public"
    ]
}


class RAGQueryService:
    """Service for section-specific RAG queries and extraction."""
    
    def __init__(self):
        """Initialize agents."""
        self.historian = HistorianAgent()
        self.pm = PMAgent()
        self.auditor = AuditorAgent()
        self.tech_lead = TechLeadAgent()
        self.strategist = StrategistAgent()
    
    async def retrieve_context(
        self,
        section: str,
        client_id: str,
        project_id: str,
        project_name: str = None,
        n_results: int = 15
    ) -> str:
        """
        Unified Fusion Retrieval for a section.
        
        Fetches context from:
        1. Explicitly tagged project data (Basecamp, Files, Drive)
        2. Global semantic matches for Project Name (Emails, Archive)
        3. Cross-source semantic matches for the specific section query
        """
        queries = SECTION_QUERIES.get(section, [])
        if not queries:
            return ""
        
        all_chunks = []
        
        logging.info(f"Querying vector store for section {section}...")
        try:
            # 1. DIRECT PROJECT SEARCH (Multi-source, project_name based)
            # Don't filter by client_id/project_id as they're MongoDB identifiers
            # Use project_name for cross-source matching
            project_chunks = await vector_store.query(
                query_text=queries,
                # Remove client_id and project_id filters for multi-source search
                extra_filters={"project_name": project_name} if project_name else None,
                n_results=50 # Semantic Broad Net (Fetch larger pool for re-ranking)
            )
            logging.info(f"Direct query for '{project_name}' returned {len(project_chunks)} chunks")
            for c in project_chunks:
                c["fusion_type"] = "Direct Sync"
                all_chunks.append(c)

            # 1.5 DEEP CONTENT RETRIEVAL (Fallback if Direct Sync is sparse)
            if project_name and len(project_chunks) < 5:
                logging.info(f"Direct sync sparse ({len(project_chunks)}). Attempting Deep Content Search for '{project_name}'")
                deep_chunks = await vector_store.query(
                    query_text=queries,
                    # We relax the strict project_id filter here to find "lost" chunks
                    # but we ENFORCE that the text content MUST contain the project name.
                    n_results=n_results,
                    content_filter_str=project_name
                )
                logging.info(f"Deep Content Search returned {len(deep_chunks)} chunks")
                for c in deep_chunks:
                    c["fusion_type"] = "Deep Content Match"
                    all_chunks.append(c)

            # 2. SEMANTIC PROJECT SEARCH (Global Pool)
            if project_name:
                name_queries = [f"{project_name} {q}" for q in queries]
                semantic_chunks = await vector_store.query(
                    query_text=name_queries,
                    n_results=30 # Semantic Broad Net
                )
                logging.info(f"Semantic query returned type: {type(semantic_chunks)}")
                for c in semantic_chunks:
                    c["fusion_type"] = "Semantic Match"
                    all_chunks.append(c)
                    
        except Exception as e:
            logging.error(f"Error inside _retrieve_for_section: {e}")
            raise e

        # 3. DEDUPLICATE & DYNAMIC RE-RANKING (The "Next Level" Logic)
        unique_chunks = []
        try:
            seen_content = set()
            ranked_candidates = []
            
            # Identify core project tokens (e.g. "ICICI Lombard GA4" -> ["ga4", "lombard", "icici"])
            # We prioritize longer, more specific tokens.
            project_tokens = set()
            if project_name:
                raw_tokens = project_name.lower().split()
                project_tokens = {t for t in raw_tokens if len(t) > 2} # Skip 'is', 'at', etc.

            for c in all_chunks:
                # Deduplicate first
                content = c["content"]
                snippet = content[:200]
                if snippet in seen_content:
                    continue
                seen_content.add(snippet)
                
                # --- HYBRID SCORING ENGINE ---
                # Base Vector Score (Normalised roughly 0.0-1.0)
                vector_score = c.get("distance", 0)
                
                # Contextual Boost
                # If the project name is "ICICI GA4", and chunk mentions "GA4", it gets a MASSIVE boost.
                content_lower = content.lower()
                subject_lower = c["metadata"].get("subject", "").lower()
                
                keyword_boost = 0.0
                if project_tokens:
                    matches = 0
                    for token in project_tokens:
                        if token in content_lower or token in subject_lower:
                            matches += 1
                    
                    # Logarithmic boost based on matches, capped at 0.3
                    if matches > 0:
                        keyword_boost = min(0.3, 0.05 * matches)
                        # Super-boost for exact phrase match if multi-word
                        if len(project_tokens) > 1 and project_name.lower() in content_lower:
                            keyword_boost += 0.2

                final_score = vector_score + keyword_boost
                c["final_score"] = final_score
                c["debug_score"] = f"V:{vector_score:.4f} + K:{keyword_boost:.4f}"
                ranked_candidates.append(c)
            
            # Sort by the new Hybrid Final Score
            ranked_candidates.sort(key=lambda x: x["final_score"], reverse=True)
            unique_chunks = ranked_candidates
            
            logging.info(f"Re-ranking complete. Top entry score: {unique_chunks[0]['debug_score'] if unique_chunks else 'N/A'}")
            
        except Exception as e:
            logging.error(f"Error during re-ranking: {e}")
            raise e

        # 4. CONSTRUCT CONTEXT WITH SOURCE DISCOVERY
        context_parts = []
        for chunk in unique_chunks[:15]:  # Optimized context window
            meta = chunk["metadata"]
            source = meta.get("filename", "unknown")
            source_type = meta.get("source", "external_archive")
            
            label = f"[{source_type.upper()} | {source}]"
            context_parts.append(f"{label}\n{chunk['content']}")
        
        return "\n\n---\n\n".join(context_parts)
    
    async def extract_all_sections(
        self,
        client_id: str,
        project_id: str,
        project_name: str = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract data for all sections using RAG.
        
        Args:
            client_id: Client identifier
            project_id: Project identifier
            
        Returns:
            Dictionary with extraction results from all agents
        """
        results = {}
        
        # 1. Universal Context & Operations (Historian + PM)
        logging.info(f"[{client_id}:{project_id}] Extracting universal_context & operations...")
        uc_context = await self.retrieve_context("universal_context", client_id, project_id, project_name)
        ops_context = await self.retrieve_context("operations", client_id, project_id, project_name)
        
        if uc_context:
            # Historian requires (document_text, rag_context)
            results["historian_output"] = await self.historian.run(uc_context, uc_context, project_name=project_name)
            logging.info(f"[RAG] Historian extracted: {list(results.get('historian_output', {}).keys())}")
        
        if ops_context:
            # PM requires (document_text, existing_tasks)
            results["pm_output"] = await self.pm.run(ops_context, "[]", project_name=project_name)
            logging.info(f"[RAG] PM extracted: {list(results.get('pm_output', {}).keys())}")

        # 2. Technical (Tech Lead)
        logging.info(f"[{client_id}:{project_id}] Extracting technical...")
        tech_context = await self.retrieve_context("technical", client_id, project_id, project_name)
        
        if tech_context:
            results["tech_lead_output"] = await self.tech_lead.run(tech_context, project_name=project_name)
            logging.info(f"[RAG] Tech Lead extracted: {list(results.get('tech_lead_output', {}).keys())}")
        
        # 3. Commercial (Auditor)
        logging.info(f"[{client_id}:{project_id}] Extracting commercial...")
        commercial_context = await self.retrieve_context("commercial", client_id, project_id, project_name)
        
        if commercial_context:
            results["auditor_output"] = await self.auditor.run(commercial_context, project_name=project_name)
            logging.info(f"[RAG] Auditor extracted: {list(results.get('auditor_output', {}).keys())}")
        
        # 4. Strategy & Marketing (Strategist)
        logging.info(f"[{client_id}:{project_id}] Extracting strategy...")
        strategy_context = await self.retrieve_context("strategy", client_id, project_id, project_name)
        marketing_context = await self.retrieve_context("marketing", client_id, project_id, project_name)
        
        combined_strategy = f"{strategy_context}\n\n{marketing_context}"
        if combined_strategy.strip():
            results["strategist_output"] = await self.strategist.run(combined_strategy, project_name=project_name)
            logging.info(f"[RAG] Strategist extracted: {list(results.get('strategist_output', {}).keys())}")
        
        return results


# Singleton instance
rag_service = RAGQueryService()