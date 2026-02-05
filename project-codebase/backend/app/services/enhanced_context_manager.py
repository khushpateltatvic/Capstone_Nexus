"""
Enhanced Context Management Service with Better Stakeholder Matching
Handles identity resolution and RBAC integration
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from app.models.domain.core_entities import Client, Project
from app.models.domain.document_references import (
    InternalStakeholder, ClientStakeholder, ProjectAssignment, 
    DocumentReference, DocumentSource
)
from app.models.domain.rbac import EnhancedUser, StakeholderIdentity, AccessLevel, Permission
from app.core.logging_config import logger

class EnhancedContextManager:
    """Enhanced context management with better identity ma