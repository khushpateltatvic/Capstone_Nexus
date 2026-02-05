from fastapi import APIRouter
from app.models.schemas.ingestion import IngestionRequest
from app.services.ingestion_service import process_text_upload

router = APIRouter()

@router.post("/upload")
async def upload_text(request: IngestionRequest):
    result = await process_text_upload(request)
    return result
