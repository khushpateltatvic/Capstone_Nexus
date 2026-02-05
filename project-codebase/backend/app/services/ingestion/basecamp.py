"""
Basecamp Import Service - Enhanced Version

Features:
- Extracts ALL data types: messages, todos, schedule, chat, vault, questionnaires
- Preserves FULL content (no truncation) for 2+ years of data
- Sorts by recency - newest first
- Stores last sync timestamp in MongoDB
- Rate limiting and retry logic
"""

import json
import time
import logging
import httpx
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from app.core.config import settings


class BasecampService:
    """Enhanced service for importing all data from Basecamp projects."""
    
    def __init__(self):
        self.enabled = bool(settings.ENABLE_BASECAMP and settings.BASECAMP_ACCESS_TOKEN and settings.BASECAMP_ACCOUNT_ID)
        self.base_url = "https://3.basecampapi.com"
        self.headers = {}
        self.request_delay = 1.0
        self.max_retries = 5
        self.retry_delay = 5
        self._db = None
        self.logger = logging.getLogger(__name__)  # Add logger attribute
        
        # Enhanced logging for initialization
        self.logger.info("=== BASECAMP SERVICE INITIALIZATION ===")
        self.logger.info(f"ENABLE_BASECAMP: {getattr(settings, 'ENABLE_BASECAMP', 'NOT_SET')}")
        self.logger.info(f"BASECAMP_ACCESS_TOKEN: {'SET' if getattr(settings, 'BASECAMP_ACCESS_TOKEN', None) else 'NOT_SET'}")
        self.logger.info(f"BASECAMP_ACCOUNT_ID: {getattr(settings, 'BASECAMP_ACCOUNT_ID', 'NOT_SET')}")
        self.logger.info(f"BASECAMP_USER_AGENT: {getattr(settings, 'BASECAMP_USER_AGENT', 'NOT_SET')}")
        self.logger.info(f"BASECAMP_PROJECT_IDS: {getattr(settings, 'BASECAMP_PROJECT_IDS', 'NOT_SET')}")
        
        if self.enabled:
            self.headers = {
                "Authorization": f"Bearer {settings.BASECAMP_ACCESS_TOKEN}",
                "User-Agent": settings.BASECAMP_USER_AGENT,
                "Content-Type": "application/json"
            }
            self.account_id = settings.BASECAMP_ACCOUNT_ID
            self.project_ids = [p.strip() for p in (settings.BASECAMP_PROJECT_IDS or "").split(",") if p.strip()]
            self.logger.info(f"✅ Basecamp service ENABLED with {len(self.project_ids)} projects: {self.project_ids}")
            self.logger.info(f"Account ID: {self.account_id}")
            self.logger.info(f"Base URL: {self.base_url}")
        else:
            self.account_id = None
            self.project_ids = []
            self.logger.warning("❌ Basecamp service DISABLED - missing configuration")
        
        self.logger.info("=== END BASECAMP INITIALIZATION ===")
        self.logger.info("")

    async def _get_db(self):
        """Get database connection."""
        if self._db is None:
            from app.core.database import get_database
            try:
                self._db = await get_database()
                if self._db is None:
                    self.logger.error("❌ Database connection returned None")
                    raise Exception("Database connection failed - returned None")
                self.logger.debug("✅ Database connection established for Basecamp service")
            except Exception as e:
                self.logger.error(f"❌ Failed to get database connection: {e}")
                raise
        return self._db

    async def get_last_sync_time(self, project_id: str) -> Optional[datetime]:
        """Get last sync timestamp for a project from MongoDB."""
        self.logger.debug(f"🔍 Getting last sync time for project: {project_id}")
        try:
            db = await self._get_db()
            if db is None:
                self.logger.error(f"❌ Database connection is None for project {project_id}")
                return None
                
            # Check if the collection exists and is accessible
            if not hasattr(db, 'basecamp_sync_state'):
                self.logger.warning(f"⚠️ basecamp_sync_state collection not accessible, treating as first sync for {project_id}")
                return None
                
            record = await db.basecamp_sync_state.find_one({"project_id": project_id})
            if record and record.get("last_sync"):
                last_sync = datetime.fromisoformat(record["last_sync"].replace("Z", "+00:00"))
                self.logger.info(f"📅 Last sync for {project_id}: {last_sync.isoformat()}")
                return last_sync
            else:
                self.logger.info(f"📅 No previous sync found for project: {project_id}")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error getting last sync time for {project_id}: {e}")
            # Return None instead of raising - this allows the sync to continue as a first-time sync
            return None

    async def set_last_sync_time(self, project_id: str, sync_time: datetime):
        """Save last sync timestamp for a project."""
        self.logger.debug(f"💾 Setting last sync time for project {project_id}: {sync_time.isoformat()}")
        try:
            db = await self._get_db()
            if db is None:
                self.logger.error(f"❌ Database connection is None, cannot save sync time for {project_id}")
                return
                
            result = await db.basecamp_sync_state.update_one(
                {"project_id": project_id},
                {"$set": {
                    "project_id": project_id,
                    "last_sync": sync_time.isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            self.logger.info(f"✅ Sync time saved for {project_id} - Modified: {result.modified_count}, Upserted: {result.upserted_id is not None}")
        except Exception as e:
            self.logger.error(f"❌ Error saving sync time for {project_id}: {e}")
            # Don't raise the exception - sync can continue even if we can't save the timestamp

    async def _get(self, client: httpx.AsyncClient, url: str, retry_count: int = 0) -> Optional[Any]:
        """Fetch data from Basecamp API with retry logic using httpx."""
        self.logger.debug(f"🌐 API Request: {url} (attempt {retry_count + 1})")
        
        try:
            response = await client.get(url, headers=self.headers, timeout=60.0)
            
            self.logger.debug(f"📡 Response: {response.status_code} for {url}")
            
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', self.retry_delay * 2))
                self.logger.warning(f"⏳ Basecamp rate limited. Waiting {wait_time}s (try {retry_count+1}/{self.max_retries})...")
                await asyncio.sleep(wait_time)
                if retry_count < self.max_retries:
                    return await self._get(client, url, retry_count + 1)
                self.logger.error(f"❌ Max retries exceeded for rate limiting: {url}")
                return None
            
            if response.status_code == 404:
                self.logger.warning(f"🔍 Resource not found (404): {url}")
                return None
                
            if response.status_code == 401:
                self.logger.error(f"🔐 Unauthorized (401): {url} - Check access token and permissions")
                return None
            
            if response.status_code != 200:
                self.logger.error(f"❌ HTTP {response.status_code} for {url}: {response.text[:200]}")
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    return await self._get(client, url, retry_count + 1)
                return None
            
            # Non-blocking delay
            await asyncio.sleep(self.request_delay)
            data = response.json()
            self.logger.debug(f"✅ Successfully fetched data from {url}")
            return data
            
        except httpx.TimeoutException as e:
            self.logger.error(f"⏰ Timeout for {url}: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._get(client, url, retry_count + 1)
            return None
        except httpx.RequestError as e:
            self.logger.error(f"🌐 Request error for {url}: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._get(client, url, retry_count + 1)
            return None
        except Exception as e:
            self.logger.error(f"❌ Unexpected error for {url}: {e}")
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                return await self._get(client, url, retry_count + 1)
            return None

    async def _get_paginated(self, client: httpx.AsyncClient, url: str, since: Optional[datetime] = None, max_pages: int = 200) -> List[Any]:
        """Fetch ALL pages for complete data extraction."""
        self.logger.debug(f"📄 Starting paginated fetch: {url}")
        if since:
            self.logger.debug(f"📅 Filtering since: {since.isoformat()}")
            
        all_data = []
        
        if since:
            since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")
            url = f"{url}{'&' if '?' in url else '?'}updated_since={since_str}"
            self.logger.debug(f"🔗 URL with since filter: {url}")
        
        current_url = url
        page = 1
        
        while current_url and page <= max_pages:
            self.logger.debug(f"📄 Fetching page {page}/{max_pages}...")
            data = await self._get(client, current_url)
            if data is None:
                self.logger.warning(f"⚠️ No data returned for page {page}")
                break
            if isinstance(data, list):
                all_data.extend(data)
                self.logger.debug(f"📄 Page {page}: {len(data)} items")
                if len(data) == 0:
                    self.logger.debug(f"📄 Empty page {page}, stopping pagination")
                    break
                current_url = f"{url}{'&' if '?' in url else '?'}page={page + 1}"
                page += 1
            else:
                all_data.append(data)
                self.logger.debug(f"📄 Single item response, stopping pagination")
                break
        
        self.logger.info(f"📄 Paginated fetch complete: {len(all_data)} total items from {page-1} pages")
        return all_data

    async def get_all_projects(self, client: httpx.AsyncClient) -> List[Dict]:
        """Fetch all projects accessible to this account."""
        if not self.enabled:
            return []
        url = f"{self.base_url}/{self.account_id}/projects.json"
        return await self._get_paginated(client, url) or []

    async def _fetch_comments(self, client: httpx.AsyncClient, bucket_id: str, recording_id: int) -> List[Dict]:
        """Fetch ALL comments for a recording."""
        url = f"{self.base_url}/{self.account_id}/buckets/{bucket_id}/recordings/{recording_id}/comments.json"
        return await self._get_paginated(client, url) or []

    async def _fetch_vault_contents(self, client: httpx.AsyncClient, project_id: str, vault_id: int, since: Optional[datetime] = None) -> Dict:
        """Fetch documents and uploads from vault recursively."""
        result = {"documents": [], "uploads": []}
        
        # Fetch documents
        docs_url = f"{self.base_url}/{self.account_id}/buckets/{project_id}/vaults/{vault_id}/documents.json"
        documents = await self._get_paginated(client, docs_url, since)
        for doc in documents:
            if isinstance(doc, dict):
                doc_id = doc.get("id")
                if doc_id:
                    full_doc = await self._get(client, f"{self.base_url}/{self.account_id}/buckets/{project_id}/documents/{doc_id}.json")
                    if full_doc:
                        result["documents"].append(full_doc)
        
        # Fetch uploads
        uploads_url = f"{self.base_url}/{self.account_id}/buckets/{project_id}/vaults/{vault_id}/uploads.json"
        uploads = await self._get_paginated(client, uploads_url, since)
        for upload in uploads:
            if isinstance(upload, dict):
                result["uploads"].append(upload)
        
        return result

    async def export_project(self, client: httpx.AsyncClient, project_id: str, full_sync: bool = False) -> Dict[str, Any]:
        """Export ALL project data with FULL content extraction."""
        self.logger.info(f"🚀 === STARTING BASECAMP PROJECT EXPORT ===")
        self.logger.info(f"📋 Project ID: {project_id}")
        self.logger.info(f"🔄 Full sync: {full_sync}")
        
        start_time = datetime.now(timezone.utc)
        
        since = None
        if not full_sync:
            since = await self.get_last_sync_time(project_id)
            if since:
                self.logger.info(f"📅 Incremental sync since: {since.isoformat()}")
            else:
                self.logger.info(f"📅 No previous sync found, performing full sync")
        else:
            self.logger.info(f"📅 Full sync requested, ignoring previous sync times")
        
        project_url = f"{self.base_url}/{self.account_id}/projects/{project_id}.json"
        self.logger.info(f"🔗 Fetching project details: {project_url}")
        project = await self._get(client, project_url)
        
        if not project:
            self.logger.error(f"❌ Project {project_id} not found or inaccessible")
            return {}
        
        self.logger.info(f"✅ Project found: {project.get('name', 'Unknown')}")
        
        result = {
            "project": project,
            "people": [],
            "messages": [],
            "todos": [],
            "schedule": [],
            "chat": [],
            "documents": [],
            "questionnaires": [],
            "is_incremental": since is not None,
            "since": since.isoformat() if since else None
        }
        
        # Fetch people
        self.logger.info("👥 === FETCHING PEOPLE ===")
        people_url = f"{self.base_url}/{self.account_id}/projects/{project_id}/people.json"
        result["people"] = await self._get_paginated(client, people_url, since)
        self.logger.info(f"👥 Found {len(result['people'])} people")
        
        # Process ALL dock tools
        dock_tools = project.get("dock", [])
        self.logger.info(f"🛠️ === PROCESSING {len(dock_tools)} DOCK TOOLS ===")
        
        for i, tool in enumerate(dock_tools, 1):
            name = tool.get("name", "")
            url = tool.get("url", "")
            enabled = tool.get("enabled", False)
            
            self.logger.info(f"🛠️ [{i}/{len(dock_tools)}] Tool: {name} - Enabled: {enabled}")
            
            if not enabled or not url:
                self.logger.warning(f"⏭️ Skipping {name} (disabled or no URL)")
                continue
            
            self.logger.info(f"🔄 Processing {name}...")
            
            try:
                if name == "message_board":
                    self.logger.info("💬 === PROCESSING MESSAGE BOARD ===")
                    messages = await self._get_paginated(client, url.replace('.json', '') + '/messages.json', since)
                    self.logger.info(f"💬 Found {len(messages)} messages")
                    
                    for j, msg in enumerate(messages, 1):
                        if isinstance(msg, dict) and msg.get("id"):
                            self.logger.debug(f"💬 Processing message {j}/{len(messages)}: {msg.get('subject', 'No subject')}")
                            # Get full message details
                            full_msg = await self._get(client, msg.get("url")) if msg.get("url") else msg
                            comments = await self._fetch_comments(client, project_id, msg["id"])
                            result["messages"].append({
                                "message": full_msg or msg,
                                "comments": comments
                            })
                    self.logger.info(f"💬 Processed {len(result['messages'])} messages with comments")
                
                elif name == "todoset":
                    self.logger.info("✅ === PROCESSING TODO LISTS ===")
                    # Fetch ALL lists to check for updated items inside them (don't filter lists by date)
                    lists = await self._get_paginated(client, url.replace('.json', '') + '/todolists.json', None)
                    self.logger.info(f"✅ Found {len(lists)} todo lists")
                    
                    for j, lst in enumerate(lists, 1):
                        if isinstance(lst, dict) and lst.get("id"):
                            list_name = lst.get('title', 'Untitled')
                            self.logger.debug(f"✅ Processing list {j}/{len(lists)}: {list_name}")
                            
                            # Get full todolist
                            full_list = await self._get(client, f"{self.base_url}/{self.account_id}/buckets/{project_id}/todolists/{lst['id']}.json")
                            todos_url = f"{self.base_url}/{self.account_id}/buckets/{project_id}/todolists/{lst['id']}/todos.json"
                            todos = await self._get_paginated(client, todos_url, since)
                            
                            self.logger.debug(f"✅ List '{list_name}' has {len(todos)} todos")
                            
                            # Get full todo details with comments
                            full_todos = []
                            for k, todo in enumerate(todos, 1):
                                if isinstance(todo, dict) and todo.get("id"):
                                    self.logger.debug(f"✅ Processing todo {k}/{len(todos)}: {todo.get('title', 'No title')}")
                                    full_todo = await self._get(client, f"{self.base_url}/{self.account_id}/buckets/{project_id}/todos/{todo['id']}.json")
                                    comments = await self._fetch_comments(client, project_id, todo["id"])
                                    full_todos.append({
                                        "todo": full_todo or todo,
                                        "comments": comments
                                    })
                            
                            result["todos"].append({
                                "list": full_list or lst,
                                "items": full_todos
                            })
                    
                    total_todos = sum(len(t.get("items", [])) for t in result["todos"])
                    self.logger.info(f"✅ Processed {len(result['todos'])} lists with {total_todos} total todos")
                
                elif name == "schedule":
                    self.logger.info("📅 === PROCESSING SCHEDULE ===")
                    entries = await self._get_paginated(client, url.replace('.json', '') + '/entries.json', since)
                    self.logger.info(f"📅 Found {len(entries)} schedule entries")
                    
                    for j, entry in enumerate(entries, 1):
                        if isinstance(entry, dict) and entry.get("id"):
                            self.logger.debug(f"📅 Processing entry {j}/{len(entries)}: {entry.get('summary', 'No title')}")
                            full_entry = await self._get(client, f"{self.base_url}/{self.account_id}/buckets/{project_id}/schedule_entries/{entry['id']}.json")
                            comments = await self._fetch_comments(client, project_id, entry["id"])
                            result["schedule"].append({
                                "entry": full_entry or entry,
                                "comments": comments
                            })
                    self.logger.info(f"📅 Processed {len(result['schedule'])} schedule entries with comments")
                
                elif name == "chat":
                    self.logger.info("💭 === PROCESSING CHAT/CAMPFIRE ===")
                    # Fetch chat/campfire lines
                    lines = await self._get_paginated(client, url.replace('.json', '') + '/lines.json', since)
                    result["chat"] = lines
                    self.logger.info(f"💭 Processed {len(result['chat'])} chat lines")
                
                elif name == "vault":
                    self.logger.info("📁 === PROCESSING VAULT/DOCUMENTS ===")
                    # Fetch documents and files
                    vault = await self._get(client, url)
                    if vault and vault.get("id"):
                        vault_content = await self._fetch_vault_contents(client, project_id, vault["id"], since)
                        result["documents"] = vault_content.get("documents", [])
                        self.logger.info(f"📁 Processed {len(result['documents'])} documents")
                    else:
                        self.logger.warning("📁 Vault not found or inaccessible")
                
                elif name == "questionnaire":
                    self.logger.info("❓ === PROCESSING QUESTIONNAIRES ===")
                    # Fetch check-in questions and answers
                    questionnaire = await self._get(client, url)
                    if questionnaire and questionnaire.get("id"):
                        q_id = questionnaire["id"]
                        questions_url = f"{self.base_url}/{self.account_id}/buckets/{project_id}/questionnaires/{q_id}/questions.json"
                        questions = await self._get_paginated(client, questions_url)
                        
                        self.logger.info(f"❓ Found {len(questions)} questions")
                        
                        for j, question in enumerate(questions, 1):
                            if isinstance(question, dict) and question.get("id"):
                                self.logger.debug(f"❓ Processing question {j}/{len(questions)}: {question.get('title', 'No title')}")
                                answers_url = f"{self.base_url}/{self.account_id}/buckets/{project_id}/questions/{question['id']}/answers.json"
                                answers = await self._get_paginated(client, answers_url, since)
                                result["questionnaires"].append({
                                    "question": question,
                                    "answers": answers
                                })
                        self.logger.info(f"❓ Processed {len(result['questionnaires'])} questionnaires")
                    else:
                        self.logger.warning("❓ Questionnaire not found or inaccessible")
                else:
                    self.logger.info(f"❓ Unknown tool type: {name} - skipping")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing {name}: {e}")
                import traceback
                self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Save sync timestamp
        await self.set_last_sync_time(project_id, start_time)
        
        # Generate metadata
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        result["_metadata"] = {
            "exported_at": start_time.isoformat(),
            "project_id": project_id,
            "project_name": project.get("name", "Unknown"),
            "duration_seconds": duration,
            "sync_type": "full" if full_sync else "incremental",
            "items_fetched": {
                "messages": len(result["messages"]),
                "todos": len(result["todos"]),
                "schedule": len(result["schedule"]),
                "chat": len(result["chat"]),
                "documents": len(result["documents"]),
                "questionnaires": len(result["questionnaires"]),
                "people": len(result["people"])
            }
        }
        
        total_items = sum(result["_metadata"]["items_fetched"].values())
        self.logger.info(f"🎉 === EXPORT COMPLETE ===")
        self.logger.info(f"📊 Total items: {total_items}")
        self.logger.info(f"⏱️ Duration: {duration:.2f} seconds")
        self.logger.info(f"📋 Project: {project.get('name', 'Unknown')}")
        
        return result

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO date string."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None

    def convert_to_text(self, export_data: Dict) -> str:
        """Convert Basecamp export to comprehensive text with FULL content, sorted by recency."""
        lines = []
        project = export_data.get("project", {})
        meta = export_data.get("_metadata", {})
        
        lines.append(f"# PROJECT: {project.get('name', 'Unknown')}")
        lines.append(f"Description: {project.get('description', 'No description')}")
        lines.append(f"Purpose: {project.get('purpose', '')}")
        lines.append(f"Created: {project.get('created_at', 'Unknown')}")
        lines.append(f"Export Date: {meta.get('exported_at', 'Unknown')}")
        lines.append(f"Sync Type: {meta.get('sync_type', 'unknown')}")
        lines.append("")
        
        # People with roles
        people = export_data.get("people", [])
        if people:
            lines.append("## TEAM MEMBERS")
            for p in people:
                if isinstance(p, dict):
                    name = p.get("name", "Unknown")
                    email = p.get("email_address", "")
                    title = p.get("title", "")
                    lines.append(f"- {name} ({email}) - {title}")
            lines.append("")
        
        # Messages - FULL content, sorted by date (newest first)
        messages = export_data.get("messages", [])
        if messages:
            # Sort by date descending
            sorted_msgs = sorted(messages, key=lambda m: m.get("message", {}).get("created_at", ""), reverse=True)
            lines.append("## MESSAGES & ANNOUNCEMENTS")
            for m in sorted_msgs:
                msg = m.get("message", {}) if isinstance(m, dict) else {}
                subject = msg.get("subject") or msg.get("title", "No subject")
                creator = msg.get("creator", {}).get("name", "Unknown")
                date = msg.get("created_at", "Unknown")
                content = msg.get("content", "")  # FULL content
                
                lines.append(f"### {subject}")
                lines.append(f"From: {creator} | Date: {date}")
                lines.append("")
                if content:
                    lines.append(content)  # Full content, no truncation
                
                # Include all comments
                for c in m.get("comments", []):
                    if isinstance(c, dict):
                        c_creator = c.get("creator", {}).get("name", "Unknown")
                        c_date = c.get("created_at", "")
                        c_content = c.get("content", "")
                        lines.append(f"\n  > Comment by {c_creator} ({c_date}):")
                        lines.append(f"  > {c_content}")
                
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # Todos - FULL details
        todos = export_data.get("todos", [])
        if todos:
            lines.append("## TASKS & TO-DOS")
            for t in todos:
                lst = t.get("list", {}) if isinstance(t, dict) else {}
                items = t.get("items", [])
                
                lines.append(f"### {lst.get('title', 'Untitled List')}")
                lines.append(f"Description: {lst.get('description', '')}")
                lines.append("")
                
                for item_data in items:
                    item = item_data.get("todo", {}) if isinstance(item_data, dict) else {}
                    status = "✅ DONE" if item.get("completed") else "⬜ PENDING"
                    title = item.get("title", "No title")
                    description = item.get("description", "")
                    due = item.get("due_on", "")
                    assignees = ", ".join([a.get("name", "") for a in item.get("assignees", [])])
                    
                    lines.append(f"  {status}: {title}")
                    if description:
                        lines.append(f"    Description: {description}")
                    if due:
                        lines.append(f"    Due: {due}")
                    if assignees:
                        lines.append(f"    Assigned to: {assignees}")
                    
                    # Include comments on todos
                    for c in item_data.get("comments", []):
                        if isinstance(c, dict):
                            lines.append(f"    > Comment: {c.get('content', '')}")
                    lines.append("")
                
                lines.append("")
        
        # Schedule entries
        schedule = export_data.get("schedule", [])
        if schedule:
            lines.append("## SCHEDULE & EVENTS")
            sorted_schedule = sorted(schedule, key=lambda e: e.get("entry", {}).get("starts_at", ""), reverse=True)
            for s in sorted_schedule:
                entry = s.get("entry", {}) if isinstance(s, dict) else s
                summary = entry.get("summary", "No title")
                starts = entry.get("starts_at", "TBD")
                ends = entry.get("ends_at", "")
                description = entry.get("description", "")
                participants = ", ".join([p.get("name", "") for p in entry.get("participants", [])])
                
                lines.append(f"- **{summary}**")
                lines.append(f"  When: {starts} - {ends}")
                if description:
                    lines.append(f"  Details: {description}")
                if participants:
                    lines.append(f"  Participants: {participants}")
                lines.append("")
        
        # Chat/Campfire messages
        chat = export_data.get("chat", [])
        if chat:
            lines.append("## CHAT HISTORY")
            sorted_chat = sorted(chat, key=lambda c: c.get("created_at", ""), reverse=True)
            for c in sorted_chat[:500]:  # Recent 500 chat messages
                if isinstance(c, dict):
                    creator = c.get("creator", {}).get("name", "Unknown")
                    date = c.get("created_at", "")
                    content = c.get("content", "")
                    lines.append(f"[{date}] {creator}: {content}")
            lines.append("")
        
        # Documents
        documents = export_data.get("documents", [])
        if documents:
            lines.append("## DOCUMENTS")
            for doc in documents:
                if isinstance(doc, dict):
                    title = doc.get("title", "Untitled")
                    content = doc.get("content", "")
                    created = doc.get("created_at", "")
                    
                    lines.append(f"### {title}")
                    lines.append(f"Created: {created}")
                    lines.append("")
                    if content:
                        lines.append(content)  # Full document content
                    lines.append("")
                    lines.append("---")
                    lines.append("")
        
        # Questionnaires/Check-ins
        questionnaires = export_data.get("questionnaires", [])
        if questionnaires:
            lines.append("## CHECK-INS & SURVEYS")
            for q in questionnaires:
                question = q.get("question", {})
                answers = q.get("answers", [])
                
                lines.append(f"### {question.get('title', 'Question')}")
                lines.append("")
                
                sorted_answers = sorted(answers, key=lambda a: a.get("created_at", ""), reverse=True)
                for a in sorted_answers:
                    if isinstance(a, dict):
                        responder = a.get("creator", {}).get("name", "Unknown")
                        date = a.get("created_at", "")
                        content = a.get("content", "")
                        lines.append(f"  - {responder} ({date}): {content}")
                lines.append("")
        
        return "\n".join(lines)

    async def sync_all_projects(self, full_sync: bool = False) -> Dict[str, Any]:
        """Sync all configured Basecamp projects with full data extraction."""
        self.logger.info(f"🚀 === STARTING BASECAMP SYNC ===")
        self.logger.info(f"🔄 Full sync: {full_sync}")
        self.logger.info(f"📋 Projects to sync: {self.project_ids}")
        
        if not self.enabled:
            self.logger.warning("❌ Basecamp sync disabled - not configured")
            return {"status": "disabled", "message": "Basecamp not configured"}
        
        if not self.project_ids:
            self.logger.warning("❌ No project IDs configured")
            return {"status": "error", "message": "No project IDs configured"}
        
        results = {"successful": [], "failed": [], "documents": [], "sync_type": "full" if full_sync else "incremental"}
        
        async with httpx.AsyncClient() as client:
            self.logger.info(f"🌐 HTTP client created, starting project sync...")
            
            for i, project_id in enumerate(self.project_ids, 1):
                self.logger.info(f"📋 === PROJECT {i}/{len(self.project_ids)}: {project_id} ===")
                
                try:
                    export_data = await self.export_project(client, project_id, full_sync=full_sync)
                    if export_data and export_data.get("_metadata"):
                        # Converting to text is CPU bound but fast enough, or we can use to_thread if massive
                        text_content = self.convert_to_text(export_data)
                        meta = export_data.get("_metadata", {})
                        
                        items = meta.get("items_fetched", {})
                        total_items = sum(items.values()) if items else 0
                        
                        if total_items > 0 or full_sync:
                            results["successful"].append(project_id)
                            results["documents"].append({
                                "project_id": project_id,
                                "project_name": meta.get("project_name", project_id),
                                "content": text_content,
                                "metadata": meta
                            })
                            self.logger.info(f"✅ SUCCESS: Extracted {total_items} items from {meta.get('project_name')}")
                        else:
                            results["successful"].append(project_id)
                            self.logger.info(f"✅ SUCCESS: No new updates for project {project_id}")
                    else:
                        results["failed"].append(project_id)
                        self.logger.error(f"❌ FAILED: No data returned for project {project_id}")
                        
                except Exception as e:
                    self.logger.error(f"❌ FAILED: Basecamp sync failed for {project_id}: {e}")
                    import traceback
                    self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    results["failed"].append(project_id)
        
        # Final summary
        success_count = len(results['successful'])
        failed_count = len(results['failed'])
        docs_count = len(results['documents'])
        
        self.logger.info(f"🎉 === BASECAMP SYNC COMPLETE ===")
        self.logger.info(f"✅ Successful: {success_count}")
        self.logger.info(f"❌ Failed: {failed_count}")
        self.logger.info(f"📄 Documents with updates: {docs_count}")
        
        if failed_count > 0:
            self.logger.warning(f"⚠️ Failed projects: {results['failed']}")
        
        return results

    async def reset_sync_state(self, project_id: Optional[str] = None):
        """Reset sync state to force full sync on next run."""
        self.logger.info(f"🔄 === RESETTING SYNC STATE ===")
        
        try:
            db = await self._get_db()
            if project_id:
                result = await db.basecamp_sync_state.delete_one({"project_id": project_id})
                self.logger.info(f"✅ Reset sync state for project {project_id} - Deleted: {result.deleted_count}")
            else:
                result = await db.basecamp_sync_state.delete_many({})
                self.logger.info(f"✅ Reset sync state for ALL projects - Deleted: {result.deleted_count}")
        except Exception as e:
            self.logger.error(f"❌ Error resetting sync state: {e}")
            raise


    async def get_recent_activity(self, project_id: str, limit: int = 10) -> List[str]:
        """
        Fetch recent comments/messages for sentiment analysis.
        Returns a list of strings (content).
        """
        if not self.enabled:
            return []
            
        activity = []
        async with httpx.AsyncClient() as client:
            # 1. Get Message Board URL
            project_url = f"{self.base_url}/{self.account_id}/projects/{project_id}.json"
            project = await self._get(client, project_url)
            if not project:
                return []

            # 2. Get Messages
            for tool in project.get("dock", []):
                if tool.get("name") == "message_board" and tool.get("enabled"):
                    msgs_url = tool.get("url").replace('.json', '') + '/messages.json'
                    messages = await self._get(client, msgs_url) # First page only
                    if messages and isinstance(messages, list):
                        for m in messages[:limit]:
                            if isinstance(m, dict):
                                title = m.get("subject", "") or m.get("title", "")
                                content = m.get("content", "") # This might be HTML
                                # Ideally clean HTML, but raw text ok for LLM often
                                activity.append(f"Message: {title}\n{content}")
                                
                elif tool.get("name") == "chat" and tool.get("enabled"):
                     chat_url = tool.get("url").replace('.json', '') + '/lines.json'
                     lines = await self._get(client, chat_url)
                     if lines and isinstance(lines, list):
                         for l in lines[:limit]:
                             if isinstance(l, dict):
                                 activity.append(f"Chat: {l.get('content', '')}")
                                 
        return activity[:limit]


# Singleton instance
basecamp_service = BasecampService()
