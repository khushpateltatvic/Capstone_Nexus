"""
Comprehensive Context Management Service
Handles get_or_create for all entities to prevent duplicates and maintain context
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.domain.core_entities import Client, Project
from app.models.domain.document_references import (
    InternalStakeholder, ClientStakeholder, ProjectAssignment, 
    DocumentReference, DocumentSource
)
from app.core.logging_config import logger

class ContextManager:
    """Centralized context management for all entities"""
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for comparison (lowercase, stripped)"""
        return " ".join(name.lower().split())

    @staticmethod
    async def get_or_create_client(client_name: str, **kwargs) -> Optional[Client]:
        """Get or create client by name"""
        if not client_name or client_name == "unknown":
            return None
        
        # First try to find existing client
        client = await Client.find_one(Client.name == client_name)
        if client:
            logger.info(f"Using existing Client: {client_name} with ID: {client.id}")
            return client
        
        # Create new client only if it doesn't exist
        try:
            client_data = {"name": client_name, **kwargs}
            client = Client(**client_data)
            await client.insert()
            logger.info(f"Created new Client: {client_name} with ID: {client.id}")
            return client
        except Exception as e:
            # Handle duplicate key error (if unique constraint is violated)
            if "duplicate key" in str(e).lower():
                # Try to find the client again (race condition handling)
                client = await Client.find_one(Client.name == client_name)
                if client:
                    logger.info(f"Found existing Client after duplicate error: {client_name} with ID: {client.id}")
                    return client
            logger.error(f"Error creating client {client_name}: {e}")
            raise

    @staticmethod
    async def get_or_create_project(project_name: str, client: Client, **kwargs) -> Optional[Project]:
        """Get or create project by name and client reference"""
        if not project_name or not client:
            return None
        
        # First try to find existing project for this client
        project = await Project.find_one(Project.name == project_name, Project.client.id == client.id)
        if project:
            logger.info(f"Using existing Project: {project_name} with ID: {project.id}")
            return project
        
        # Create new project only if it doesn't exist for this client
        project_data = {"name": project_name, "client": client, **kwargs}
        project = Project(**project_data)
        await project.insert()
        logger.info(f"Created new Project: {project_name} with ID: {project.id} for Client: {client.name}")
        return project

    @staticmethod
    async def get_or_create_internal_stakeholder(name: str, email: Optional[str] = None, **kwargs) -> Optional[InternalStakeholder]:
        """Get or create internal stakeholder by email (primary) or name + additional context"""
        if not name:
            return None
        
        # First try to find by email (most reliable)
        if email:
            stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == email)
            if stakeholder:
                logger.info(f"Using existing Internal Stakeholder by email: {name} ({email}) with ID: {stakeholder.id}")
                return stakeholder
        
        # If no email or not found by email, try to find by name + context
        # Look for exact name match first
        stakeholders_with_name = await InternalStakeholder.find(InternalStakeholder.name == name).to_list()
        
        if len(stakeholders_with_name) == 1:
            # Only one person with this name, use them
            stakeholder = stakeholders_with_name[0]
            logger.info(f"Using existing Internal Stakeholder by unique name: {name} with ID: {stakeholder.id}")
            return stakeholder
        elif len(stakeholders_with_name) > 1:
            # Multiple people with same name, try to match by additional context
            role = kwargs.get("role")
            department = kwargs.get("department")
            
            for stakeholder in stakeholders_with_name:
                # Match by role and department if provided
                if role and department:
                    if stakeholder.role == role and stakeholder.department == department:
                        logger.info(f"Using existing Internal Stakeholder by name+role+dept: {name} with ID: {stakeholder.id}")
                        return stakeholder
                # Match by role only
                elif role and stakeholder.role == role:
                    logger.info(f"Using existing Internal Stakeholder by name+role: {name} with ID: {stakeholder.id}")
                    return stakeholder
                # Match by department only
                elif department and stakeholder.department == department:
                    logger.info(f"Using existing Internal Stakeholder by name+dept: {name} with ID: {stakeholder.id}")
                    return stakeholder
            
            # If we have multiple matches and no clear winner, create new one
            logger.warning(f"Multiple Internal Stakeholders named '{name}' found, creating new one with email: {email}")
            # Don't return here, continue to create new stakeholder
        else:
             # Fuzzy Deduplication: Check if any existing name contains this name or vice versa (e.g. "John" vs "John Doe")
             # This is a bit expensive but robust for the user's request "John" vs "John Doe"
             # Only do this if we are creating a NEW stakeholder (count is 0)
             # Get all internal stakeholders? No, too expensive.
             # Limit by regex?
             normalized = ContextManager._normalize_name(name)
             if len(normalized) > 3: # Only fuzzy match if name is substantial
                 potential_matches = await InternalStakeholder.find({"name": {"$regex": normalized, "$options": "i"}}).to_list()
                 if potential_matches:
                     best_match = potential_matches[0]
                     logger.info(f"Fuzzy duplicate match: '{name}' mapped to existing '{best_match.name}'")
                     return best_match
        
        # Create new stakeholder only if it doesn't exist or we can't match uniquely
        try:
            stakeholder_data = {"name": name, "email": email, **kwargs}
            stakeholder = InternalStakeholder(**stakeholder_data)
            await stakeholder.insert()
            logger.info(f"Created new Internal Stakeholder: {name} ({email}) with ID: {stakeholder.id}")
            return stakeholder
        except Exception as e:
            # Handle duplicate email error
            if "duplicate key" in str(e).lower() and email:
                stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == email)
                if stakeholder:
                    logger.info(f"Found existing Internal Stakeholder after duplicate email error: {name} ({email}) with ID: {stakeholder.id}")
                    return stakeholder
            logger.error(f"Error creating internal stakeholder {name} ({email}): {e}")
            raise

    @staticmethod
    async def get_or_create_client_stakeholder(name: str, client: Client, email: Optional[str] = None, **kwargs) -> Optional[ClientStakeholder]:
        """Get or create client stakeholder by name + client + email context"""
        if not name or not client:
            return None
        
        # First try to find by email within this client (most reliable)
        if email:
            stakeholder = await ClientStakeholder.find_one(
                ClientStakeholder.email == email,
                ClientStakeholder.client.id == client.id
            )
            if stakeholder:
                logger.info(f"Using existing Client Stakeholder by email: {name} ({email}) for {client.name} with ID: {stakeholder.id}")
                return stakeholder
        
        # Try to find by name within this client
        stakeholders_with_name = await ClientStakeholder.find(
            ClientStakeholder.name == name,
            ClientStakeholder.client.id == client.id
        ).to_list()
        
        if len(stakeholders_with_name) == 1:
            # Only one person with this name at this client
            stakeholder = stakeholders_with_name[0]
            logger.info(f"Using existing Client Stakeholder by unique name: {name} for {client.name} with ID: {stakeholder.id}")
            return stakeholder
        elif len(stakeholders_with_name) > 1:
            # Multiple people with same name at same client, try to match by additional context
            role = kwargs.get("role")
            department = kwargs.get("department")
            
            for stakeholder in stakeholders_with_name:
                # Match by role and department if provided
                if role and department:
                    if stakeholder.role == role and stakeholder.department == department:
                        logger.info(f"Using existing Client Stakeholder by name+role+dept: {name} for {client.name} with ID: {stakeholder.id}")
                        return stakeholder
                # Match by role only
                elif role and stakeholder.role == role:
                    logger.info(f"Using existing Client Stakeholder by name+role: {name} for {client.name} with ID: {stakeholder.id}")
                    return stakeholder
                # Match by department only
                elif department and stakeholder.department == department:
                    logger.info(f"Using existing Client Stakeholder by name+dept: {name} for {client.name} with ID: {stakeholder.id}")
                    return stakeholder
            
            # If we have multiple matches and no clear winner, log warning and create new
            logger.warning(f"Multiple Client Stakeholders named '{name}' found at {client.name}, creating new one with email: {email}")
        else:
             # Fuzzy Deduplication within Client Context
             normalized = ContextManager._normalize_name(name)
             if len(normalized) > 3:
                 potential_matches = await ClientStakeholder.find(
                     {"name": {"$regex": normalized, "$options": "i"}, "client.$id": client.id}
                 ).to_list()
                 if potential_matches:
                     best_match = potential_matches[0]
                     logger.info(f"Fuzzy duplicate match: '{name}' mapped to existing '{best_match.name}' for client {client.name}")
                     return best_match
        
        # Create new stakeholder only if it doesn't exist for this client or we can't match uniquely
        stakeholder_data = {"name": name, "client": client, "email": email, **kwargs}
        stakeholder = ClientStakeholder(**stakeholder_data)
        await stakeholder.insert()
        logger.info(f"Created new Client Stakeholder: {name} ({email}) for {client.name} with ID: {stakeholder.id}")
        return stakeholder

    @staticmethod
    async def get_or_create_project_assignment(
        internal_stakeholder: InternalStakeholder, 
        project: Project, 
        role_in_project: str,
        **kwargs
    ) -> Optional[ProjectAssignment]:
        """Get or create project assignment"""
        if not internal_stakeholder or not project:
            return None
        
        # First try to find existing assignment
        assignment = await ProjectAssignment.find_one(
            ProjectAssignment.internal_stakeholder.id == internal_stakeholder.id,
            ProjectAssignment.project.id == project.id,
            ProjectAssignment.role_in_project == role_in_project
        )
        if assignment:
            logger.info(f"Using existing Project Assignment: {internal_stakeholder.name} -> {project.name} as {role_in_project}")
            return assignment
        
        # Create new assignment
        assignment_data = {
            "internal_stakeholder": internal_stakeholder,
            "project": project,
            "role_in_project": role_in_project,
            **kwargs
        }
        assignment = ProjectAssignment(**assignment_data)
        await assignment.insert()
        logger.info(f"Created new Project Assignment: {internal_stakeholder.name} -> {project.name} as {role_in_project}")
        return assignment

    @staticmethod
    async def get_or_create_document_reference(
        source_type: str,
        source_id: str,
        title: str,
        **kwargs
    ) -> Optional[DocumentReference]:
        """Get or create document reference"""
        if not source_type or not source_id:
            return None
        
        # First try to find existing document reference
        doc_ref = await DocumentReference.find_one(
            DocumentReference.source_type == source_type,
            DocumentReference.source_id == source_id
        )
        if doc_ref:
            # Update access tracking
            doc_ref.last_accessed = datetime.utcnow()
            doc_ref.access_count += 1
            await doc_ref.save()
            logger.info(f"Using existing Document Reference: {source_type}:{source_id} (accessed {doc_ref.access_count} times)")
            return doc_ref
        
        # Create new document reference
        doc_data = {
            "source_type": source_type,
            "source_id": source_id,
            "title": title,
            **kwargs
        }
        doc_ref = DocumentReference(**doc_data)
        await doc_ref.insert()
        logger.info(f"Created new Document Reference: {source_type}:{source_id} - {title}")
        return doc_ref

    @staticmethod
    def create_document_source(
        source_type: str,
        source_id: Optional[str] = None,
        source_url: Optional[str] = None,
        source_title: Optional[str] = None,
        source_date: Optional[datetime] = None,
        **metadata
    ) -> DocumentSource:
        """Create a DocumentSource for embedding in other documents"""
        return DocumentSource(
            source_type=source_type,
            source_id=source_id,
            source_url=source_url,
            source_title=source_title,
            source_date=source_date,
            metadata=metadata if metadata else None
        )

    @staticmethod
    async def find_stakeholder_by_email(email: str, is_internal: bool = True) -> Optional[InternalStakeholder | ClientStakeholder]:
        """Find stakeholder by email (internal or client)"""
        if not email:
            return None
        
        if is_internal:
            return await InternalStakeholder.find_one(InternalStakeholder.email == email)
        else:
            return await ClientStakeholder.find_one(ClientStakeholder.email == email)

    @staticmethod
    async def get_project_team(project: Project) -> Dict[str, List[InternalStakeholder]]:
        """Get all internal stakeholders assigned to a project, grouped by role"""
        assignments = await ProjectAssignment.find(
            ProjectAssignment.project.id == project.id,
            ProjectAssignment.active == True
        ).to_list()
        
        team = {}
        for assignment in assignments:
            role = assignment.role_in_project
            if role not in team:
                team[role] = []
            
            # Fetch the stakeholder
            stakeholder = await assignment.internal_stakeholder.fetch()
            if stakeholder:
                team[role].append(stakeholder)
        
        return team

    @staticmethod
    async def get_client_contacts(client: Client) -> List[ClientStakeholder]:
        """Get all active client stakeholders for a client"""
        return await ClientStakeholder.find(
            ClientStakeholder.client.id == client.id,
            ClientStakeholder.active == True
        ).to_list()

# Global instance
context_manager = ContextManager()