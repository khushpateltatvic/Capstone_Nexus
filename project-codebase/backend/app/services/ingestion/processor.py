"""
Document Processor Service

Features:
- Parses various file formats (PDF, DOCX, EML, TXT)
- Chunks and ingests into RAG vector store
- Triggers intelligence extraction pipeline
- Supports client/project metadata from watchdog
"""

import logging
import asyncio
import os
from app.core.memory_adapters import msg_queue
from app.services.ingestion.vector_store import vector_store
from app.services.ingestion.chunker import chunker
from app.services.ingestion.parsers.pdf_parser import PDFParser
from app.services.ingestion.parsers.doc_parser import DocParser
from app.services.ingestion.parsers.email_parser import EmailParser
from app.services.rag.query_service import rag_service
from app.services.intelligence.agents.reducer import reducer
from app.services.ingestion.parsers.text_parser import TextParser
from app.services.intelligence.graph import build_graph


class ProcessorService:
    """
    Processes documents from the message queue.
    
    Flow:
    1. Receive document from watchdog via queue
    2. Parse file content to text
    3. Chunk text into semantic segments
    4. Ingest chunks into vector store with client/project metadata
    5. Trigger RAG extraction for all sections
    6. Persist results to MongoDB
    """
    
    def __init__(self):
        self.parsers = {
            ".pdf": PDFParser(),
            ".docx": DocParser(),
            ".eml": EmailParser(),
            ".html": EmailParser(),
            ".txt": TextParser()
        }
        self.default_parser = EmailParser()

    async def _process_item(self, item: dict):
        """
        Coordinates the transformation of a raw file into intelligence.
        
        Args:
            item: Dict with keys:
                - filename: Original filename
                - content: File bytes
                - client_id: Client identifier (from folder structure)
                - project_id: Project identifier (from folder structure)
                - source: Source type (local_filesystem, gmail, drive)
        """
        filename = item.get("filename", "unknown")
        content = item.get("content")
        client_id = item.get("client_id", "default_client")
        project_id = item.get("project_id", "default_project")
        project_name = item.get("project_name")
        source = item.get("source", "unknown")

        logging.info(f"Processing: {client_id}/{project_id}/{filename} from {source}")

        # 1. Parse content based on file extension
        ext = os.path.splitext(filename)[1].lower()
        parser = self.parsers.get(ext, self.default_parser)
        
        try:
            text = parser.parse(content)
            if not text:
                logging.warning(f"No text extracted from {filename}")
                return

            # 2. Chunk the text
            metadata = {
                "client_id": client_id,
                "project_id": project_id,
                "filename": filename,
                "source": source,
                "project_name": item.get("project_name")
            }
            chunks = chunker.chunk_document(
                text=text,
                metadata=metadata
            )
            
            if not chunks:
                logging.warning(f"No chunks created from {filename}")
                return

            # 3. Add to Vector Store (RAG)
            try:
                await vector_store.add_chunks(
                    chunks=chunks,
                    client_id=client_id,
                    project_id=project_id
                )
                logging.info(f"Ingested {len(chunks)} chunks from {filename}")
            except Exception as embed_error:
                logging.error(f"❌ Failed to embed {filename}: {embed_error}")
                # Don't completely fail - continue with next document
                return

            # 4. Trigger RAG Extraction (async, non-blocking)
            try:
                asyncio.create_task(self._run_extraction(client_id, project_id, filename, project_name))
                logging.info(f"Dispatched extraction task for {client_id}/{project_id}")
            except Exception as extract_error:
                logging.warning(f"⚠️ Failed to dispatch extraction for {filename}: {extract_error}")
                # Don't fail completely - embedding was successful

        except Exception as e:
            logging.error(f"Failed to process {filename}: {e}")

    async def _run_extraction(self, client_id: str, project_id: str, filename: str, project_name: str = None):
        """
        Runs RAG extraction and persists results using LangGraph.
        """
        try:
            # Initialize Graph
            workflow = build_graph()
            if not workflow:
                logging.error("LangGraph failed to initialize")
                return

            # Initial State
            initial_state = {
                "metadata": {
                    "client_id": client_id,
                    "project_id": project_id,
                    "project_name": project_name, # Passed to graph for retrieval
                    "filename": filename
                }
            }
            
            logging.info(f"[{client_id}:{project_id}] Invoking LangGraph for extraction...")
            
            # Run Graph
            # workflow.invoke is synchronous, for async we use ainvoke
            result = await workflow.ainvoke(initial_state)
            
            final_out = result.get("final_output", {})
            logging.info(f"Extraction complete: {final_out.get('fields_updated', 0)} fields updated for {project_id}")
            
        except Exception as e:
            logging.error(f"Extraction failed for {client_id}/{project_id}: {e}")

    async def start(self):
        """
        Continuous processing loop.
        
        Pulls items from message queue and processes them.
        """
        logging.info("Ingestion Processor Service active...")
        while True:
            item = await msg_queue.dequeue()
            if item:
                await self._process_item(item)
            # Small sleep to prevent tight loop
            await asyncio.sleep(0.1)


processor = ProcessorService()
