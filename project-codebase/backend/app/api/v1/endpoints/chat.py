from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import get_nexus_answer
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access
from app.core.database import get_database

router = APIRouter()

@router.post("/ask", response_model=ChatResponse)
async def ask_nexus(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        # Validate project access if project_id is provided
        if request.project_id:
            db = await get_database()
            project = await db.projects.find_one({"project_id": request.project_id})
            
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            if not has_project_access(current_user, project):
                raise HTTPException(status_code=403, detail="You don't have access to this project")
        
        # Validate client access if client_id is provided (but no project_id)
        elif request.client_id:
            db = await get_database()
            # Check if user has access to any project under this client
            has_access = False
            async for project in db.projects.find({"client_id": request.client_id}):
                if has_project_access(current_user, project):
                    has_access = True
                    break
            
            if not has_access:
                raise HTTPException(status_code=403, detail="You don't have access to this client")
        
        # Call the chat service with project/client context
        response = await get_nexus_answer(
            query=request.message,
            client_id=request.client_id,
            project_id=request.project_id
        )
        
        return ChatResponse(
            answer=response["answer"],
            sources=response["sources"],
            project_context=response.get("project_context")
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (access control)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
