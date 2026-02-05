"""
Watchdog Service - Multi-Source Document Ingestion

Features:
- Local file poller with folder-based client/project extraction
- Gmail poller (optional, requires Google API setup)
- Drive poller (optional, requires Google API setup)
- Automatic archiving of processed files
"""

import asyncio
import os
import shutil
import logging
from typing import List, Protocol
from app.core.config import settings
from app.core.memory_adapters import msg_queue

# Optional Google imports - guarded for production stability
try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
except ImportError:
    logging.warning("Google API Client libraries not installed. Gmail/Drive pollers will wait.")

# --- Poller Interface ---
class SourcePoller(Protocol):
    async def poll(self) -> List[dict]:
        ...

# --- Local File Poller with Folder-Based Client/Project Extraction ---
class LocalFilePoller:
    """
    Polls a local directory for new documents.
    
    Folder Structure (Recommended):
        uploads/
        ├── {client_id}/
        │   ├── {project_id}/
        │   │   └── document.txt
        │   └── {project_id}/
        │       └── other_doc.pdf
        └── archived/  (processed files moved here)
    
    Fallback (Flat Files):
        uploads/
        ├── document.txt  -> client_id="default", project_id="default_project"
        └── archived/
    """
    
    def __init__(self, watch_dir: str):
        self.watch_dir = watch_dir
        self.archive_dir = os.path.join(watch_dir, "archived")
        if not os.path.exists(watch_dir):
            os.makedirs(watch_dir)
        if not os.path.exists(self.archive_dir):
            os.makedirs(self.archive_dir)
            
    async def poll(self) -> List[dict]:
        """
        Scans folder structure for documents, extracts client/project from path.
        """
        if not settings.ENABLE_LOCAL_FILES:
            return []
            
        found_files = []
        
        # Run os.listdir in thread since it can be blocking on slow filesystems
        def scan_directory():
            try:
                return os.listdir(self.watch_dir)
            except Exception:
                return []
                
        items = await asyncio.to_thread(scan_directory)
        
        # First, check for nested folder structure: client/project/file
        for item in items:
            item_path = os.path.join(self.watch_dir, item)
            
            # Skip archived folder and non-directories for nested processing
            if item == "archived":
                continue
                
            if os.path.isdir(item_path):
                # This is a client folder
                client_id = item
                
                try:
                    project_items = await asyncio.to_thread(os.listdir, item_path)
                except Exception:
                    continue

                for project_item in project_items:
                    project_path = os.path.join(item_path, project_item)
                    
                    if os.path.isdir(project_path):
                        # This is a project folder
                        project_id = project_item
                        
                        try:
                            files = await asyncio.to_thread(os.listdir, project_path)
                        except Exception:
                            continue

                        for filename in files:
                            filepath = os.path.join(project_path, filename)
                            if not os.path.isfile(filepath):
                                continue
                                
                            file_data = await self._process_file(
                                filepath, 
                                filename, 
                                client_id, 
                                project_id
                            )
                            if file_data:
                                found_files.append(file_data)
                    
                    elif os.path.isfile(project_path):
                        # File directly in client folder (no project subfolder)
                        # Use client_id as project_id too
                        file_data = await self._process_file(
                            project_path, 
                            project_item, 
                            client_id, 
                            client_id  # project_id = client_id
                        )
                        if file_data:
                            found_files.append(file_data)
            
            elif os.path.isfile(item_path):
                # Flat file in uploads root - use defaults
                file_data = await self._process_file(
                    item_path, 
                    item, 
                    "default_client", 
                    "default_project"
                )
                if file_data:
                    found_files.append(file_data)
        
        return found_files
    
    async def _process_file(
        self, 
        filepath: str, 
        filename: str, 
        client_id: str, 
        project_id: str
    ) -> dict:
        """Process a single file and archive it."""
        try:
            logging.info(f"Processing: {client_id}/{project_id}/{filename}")
            
            def read_file():
                with open(filepath, "rb") as f:
                    return f.read()

            content = await asyncio.to_thread(read_file)
            
            file_data = {
                "filename": filename,
                "content": content,
                "client_id": client_id,
                "project_id": project_id,
                "source": "local_filesystem",
                "size": len(content)
            }
            
            # Archive with folder structure preserved
            archive_path = os.path.join(self.archive_dir, client_id, project_id)
            
            def move_file():
                os.makedirs(archive_path, exist_ok=True)
                shutil.move(filepath, os.path.join(archive_path, filename))
                
            await asyncio.to_thread(move_file)
            
            return file_data
            
        except Exception as e:
            logging.error(f"Failed to process {filepath}: {e}")
            return None

# --- Gmail Poller ---
class GmailPoller:
    """
    Polls Gmail for messages with the intake label.
    
    Email Subject Convention:
        [Project Nexus] {client_id}/{project_id} - Document Title
        
    Or use Gmail labels:
        Labels: Client-Acme, Project-Alpha
    """
    
    def __init__(self):
        self.enabled = all([settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET])
        self.service = None

    async def _init_service(self):
        if self.enabled and not self.service:
            try:
                # In prod, retrieve stored refresh_token from DB or Vault
                # credentials = Credentials(token=..., refresh_token=..., client_id=..., client_secret=...)
                # self.service = build('gmail', 'v1', credentials=credentials)
                pass
            except Exception as e:
                logging.error(f"Gmail Service Init Error: {e}")

    async def poll(self) -> List[dict]:
        """Polls Gmail for messages with the intake label and downloads attachments."""
        if not self.enabled or not settings.ENABLE_GMAIL:
            return []
            
        logging.info(f"Polling Gmail for label: {settings.GMAIL_POLL_LABEL}")
        # In real production, this would:
        # 1. List messages with label 'Project-Nexus-Intake'
        # 2. Parse subject for client_id/project_id
        # 3. Get message content and attachments
        # 4. Mark message as 'Processed' label (remove intake label)
        # 5. Return attachment bytes + metadata
        return []

# --- Google Drive Poller ---
class DrivePoller:
    """
    Polls specific Drive folder for new files.
    
    Folder Structure in Drive:
        Project-Nexus-Intake/
        ├── {client_id}/
        │   └── {project_id}/
        │       └── document.pdf
    """
    
    def __init__(self):
        self.enabled = settings.DRIVE_WATCH_FOLDER_ID is not None
        self.service = None

    async def poll(self) -> List[dict]:
        """Polls specific Drive folder for new files since last check."""
        if not self.enabled or not settings.ENABLE_DRIVE:
            return []
            
        logging.info(f"Polling Google Drive Folder: {settings.DRIVE_WATCH_FOLDER_ID}")
        # Implementation logic:
        # 1. List files in watched folder
        # 2. Parse folder structure for client_id/project_id
        # 3. Download file content
        # 4. Move to processed folder
        # items = self.service.files().list(q=f"'{settings.DRIVE_WATCH_FOLDER_ID}' in parents and trashed=false").execute()
        return []

# --- Main Watchdog Service ---
class WatchdogService:
    """
    Central service that orchestrates all pollers.
    
    Usage:
        from app.services.ingestion.watchdog import watchdog
        await watchdog.trigger_sync()  # Manual trigger
        await watchdog.start()  # Background loop
    """
    
    def __init__(self):
        self.pollers: List[SourcePoller] = []
        
        if settings.ENABLE_LOCAL_FILES:
            self.pollers.append(LocalFilePoller(watch_dir="uploads"))
        
        if settings.ENABLE_GMAIL:
            self.pollers.append(GmailPoller())
            
        if settings.ENABLE_DRIVE:
            self.pollers.append(DrivePoller())

    async def trigger_sync(self):
        """Manually trigger a sync across all pollers."""
        logging.info("Executing global Watchdog sync...")
        for poller in self.pollers:
            try:
                new_items = await poller.poll()
                for item in new_items:
                    # Enqueue with extracted metadata
                    await msg_queue.enqueue(item)
                    logging.info(f"Enqueued: {item.get('client_id')}/{item.get('project_id')}/{item.get('filename')}")
            except Exception as e:
                logging.error(f"Sync failed for {type(poller).__name__}: {e}")

    async def start(self):
        """Start background polling loop."""
        logging.info("Watchdog Service active (Background Worker)")
        while True:
            await self.trigger_sync()
            await asyncio.sleep(settings.WATCHDOG_POLL_INTERVAL)

watchdog = WatchdogService()
