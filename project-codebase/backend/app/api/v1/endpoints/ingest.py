from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Any
import shutil
import os
import uuid
from app.services.ingestion.watchdog import LocalFilePoller
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/manual")
async def manual_ingest(
    client_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Manual file upload endpoint.
    Protected by JWT. Saves file to upload directory.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file sent")

    # Access Check: Does user have access to *any* project for this client?
    from app.core.database import get_database
    db = await get_database()
    has_access = False
    async for project in db.projects.find({"client_id": client_id}):
        if has_project_access(current_user, project):
            has_access = True
            break
    
    if not has_access and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="You do not have access to this client")

    # Basic size check (simulated, as we stream)
    # real impl would check Content-Length header or stream with limit
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")

    return {
        "filename": file.filename,
        "saved_as": unique_filename,
        "status": "Queued for processing",
        "job_id": str(uuid.uuid4())
    }


@router.get("/status")
async def get_ingest_status_root(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get the status of the ingestion queue.
    This is an alias for /automation/ingest/status for convenience.
    """
    from app.core.memory_adapters import msg_queue
    return {
        "queue_size": msg_queue.qsize(),
        "is_processing": msg_queue.qsize() > 0,
        "status": "In Progress" if msg_queue.qsize() > 0 else "Idle/Complete"
    }
