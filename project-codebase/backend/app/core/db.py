from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

# Import models
from app.models.domain.user import User
from app.models.domain.core_entities import Client, Project
from app.models.domain.sections import (
    UniversalContext, OperationsState, TechnicalState, CommercialState,
    StrategyState, MarketingState, MiscState
)
from app.models.domain.access_control import RolePermission
from app.models.domain.document_references import (
    InternalStakeholder, ClientStakeholder, ProjectAssignment, 
    DocumentReference, AccessControlRule
)

async def init_db():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            User,
            Client,
            Project,
            UniversalContext,
            OperationsState,
            TechnicalState,
            CommercialState,
            StrategyState,
            MarketingState,
            MiscState,
            
            # Context management and access control models
            InternalStakeholder,
            ClientStakeholder,
            ProjectAssignment,
            DocumentReference,
            RolePermission,
            AccessControlRule
        ]
    )
