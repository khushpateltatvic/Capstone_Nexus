"""
Comprehensive Access Control Service
Handles hierarchical permissions, role-based access, and data filtering
"""
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from app.models.domain.document_references import (
    InternalStakeholder, ClientStakeholder, AccessControlRule, AccessLevel
)
from app.models.domain.core_entities import Client, Project
from app.core.logging_config import logger

class AccessControlService:
    """Centralized access control management"""
    
    # Hierarchical seniority levels (higher number = more senior)
    SENIORITY_HIERARCHY = {
        "junior": 1,
        "senior": 2,
        "lead": 3,
        "manager": 4,
        "director": 5,
        "executive": 6
    }
    
    # Default permissions by seniority level
    DEFAULT_PERMISSIONS = {
        "junior": [
            "view_assigned_projects",
            "view_basic_client_info",
            "create_tasks",
            "update_own_tasks"
        ],
        "senior": [
            "view_assigned_projects",
            "view_detailed_client_info",
            "create_tasks",
            "update_tasks",
            "view_team_performance",
            "mentor_junior_staff"
        ],
        "lead": [
            "view_assigned_projects",
            "view_detailed_client_info",
            "create_tasks",
            "update_tasks",
            "assign_tasks",
            "view_team_performance",
            "manage_project_team",
            "view_project_financials_basic",
            "add_team_members"  # Leads can add team members to their projects
        ],
        "manager": [
            "view_all_department_projects",
            "view_sensitive_client_info",
            "create_tasks",
            "update_tasks",
            "assign_tasks",
            "create_projects",
            "manage_team_assignments",
            "view_project_financials",
            "approve_budgets_small",
            "add_team_members",
            "view_performance_reviews",
            "view_team_performance"
        ],
        "director": [
            "view_all_projects",
            "view_strategic_client_info",
            "create_clients",
            "manage_department",
            "view_all_financials",
            "approve_budgets_large",
            "hire_staff",
            "access_executive_reports"
        ],
        "executive": [
            "view_everything",
            "manage_everything",
            "access_board_reports",
            "approve_major_decisions",
            "set_company_strategy"
        ]
    }
    
    @staticmethod
    async def get_user_permissions(user: InternalStakeholder) -> Set[str]:
        """Get all permissions for a user based on their role and seniority"""
        permissions = set()
        
        # Add cumulative permissions based on seniority hierarchy
        user_seniority_value = AccessControlService.SENIORITY_HIERARCHY.get(user.seniority_level, 0)
        
        for level_name, level_value in AccessControlService.SENIORITY_HIERARCHY.items():
            if level_value <= user_seniority_value:
                level_perms = AccessControlService.DEFAULT_PERMISSIONS.get(level_name, [])
                permissions.update(level_perms)
        
        # Add permissions from access level
        if user.access_level:
            permissions.update(user.access_level.permissions)
        
        # Add permissions from access control rules
        rules = await AccessControlRule.find(
            AccessControlRule.active == True
        ).to_list()
        
        for rule in rules:
            if AccessControlService._rule_applies_to_user(rule, user):
                permissions.update(rule.permissions)
        
        return permissions
    
    @staticmethod
    def _rule_applies_to_user(rule: AccessControlRule, user: InternalStakeholder) -> bool:
        """Check if an access control rule applies to a user"""
        # Check role match
        if rule.applies_to_roles and user.role not in rule.applies_to_roles:
            return False
        
        # Check seniority match
        if rule.applies_to_seniority and user.seniority_level not in rule.applies_to_seniority:
            return False
        
        # Check department match
        if rule.applies_to_departments and user.department not in rule.applies_to_departments:
            return False
        
        return True
    
    @staticmethod
    async def can_user_access_client(user: InternalStakeholder, client: Client) -> bool:
        """Check if user can access a specific client"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Executives can access everything
        if "view_everything" in permissions:
            return True
        
        # Directors can access all clients
        if "view_all_projects" in permissions:
            return True
        
        # Check if user has specific client access
        if user.access_level and user.access_level.can_view_clients:
            if str(client.id) in user.access_level.can_view_clients:
                return True
        
        # Check if user is assigned to any projects for this client
        from app.models.domain.document_references import ProjectAssignment
        assignments = await ProjectAssignment.find(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.active == True
        ).to_list()
        
        for assignment in assignments:
            project = await assignment.project.fetch()
            if project:
                project_client = await project.client.fetch()
                if project_client and project_client.id == client.id:
                    return True
        
        return False
    
    @staticmethod
    async def can_user_access_project(user: InternalStakeholder, project: Project) -> bool:
        """Check if user can access a specific project"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Executives can access everything
        if "view_everything" in permissions:
            return True
        
        # Directors can access all projects
        if "view_all_projects" in permissions:
            return True
        
        # Managers can access department projects
        if "view_all_department_projects" in permissions:
            # Check if any team member on this project is in user's department
            from app.models.domain.document_references import ProjectAssignment
            assignments = await ProjectAssignment.find(
                ProjectAssignment.project.id == project.id,
                ProjectAssignment.active == True
            ).to_list()
            
            for assignment in assignments:
                team_member = await assignment.internal_stakeholder.fetch()
                if team_member and hasattr(team_member, 'department') and team_member.department == user.department:
                    return True
        
        return assignment is not None

    @staticmethod
    async def can_user_view_section(user: InternalStakeholder, project: Project, section_key: str) -> bool:
        """Check if user can view a specific business section for a project"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Executives can view everything
        if "view_everything" in permissions:
            return True
            
        # Check Project Assignment for custom overrides
        from app.models.domain.document_references import ProjectAssignment
        assignment = await ProjectAssignment.find_one(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.project.id == project.id,
            ProjectAssignment.active == True
        )
        
        if assignment and section_key in assignment.custom_view_access:
            return True
            
        # Check Global Role Matrix via RolePermission
        from app.models.domain.access_control import RolePermission
        role_perm = await RolePermission.find_one(
            RolePermission.role == user.role,
            RolePermission.department == user.department
        )
        
        if role_perm:
            # Map section_key to matrix sub-keys if necessary or check direct
            # For simplicity, we'll assume the matrix has keys starting with section index
            # or matching the module name. 
            # Looking at seed script, matrix has '1_client_profile', '2_escalation', etc.
            # We'll see if ANY key starting with the section index is "V" or "E"
            prefix = section_key.split("_")[0]
            for key, val in role_perm.permissions.items():
                if key.startswith(prefix) and val in ["V", "E"]:
                    return True
        
        return False

    @staticmethod
    async def can_user_edit_section(user: InternalStakeholder, project: Project, section_key: str) -> bool:
        """Check if user can edit a specific business section for a project"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        if "manage_everything" in permissions:
            return True
            
        from app.models.domain.document_references import ProjectAssignment
        assignment = await ProjectAssignment.find_one(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.project.id == project.id,
            ProjectAssignment.active == True
        )
        
        if assignment and section_key in assignment.custom_edit_access:
            return True
            
        from app.models.domain.access_control import RolePermission
        role_perm = await RolePermission.find_one(
            RolePermission.role == user.role,
            RolePermission.department == user.department
        )
        
        if role_perm:
            prefix = section_key.split("_")[0]
            for key, val in role_perm.permissions.items():
                if key.startswith(prefix) and val == "E":
                    return True
        
        return False
    
    @staticmethod
    async def can_user_add_team_member(user: InternalStakeholder, project: Project) -> bool:
        """Check if user can add team members to a project"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Check general permission
        if "add_team_members" not in permissions:
            return False
        
        # Check if user can access the project
        if not await AccessControlService.can_user_access_project(user, project):
            return False
        
        # Managers and above can add team members to any project they can access
        if user.seniority_level in ["manager", "director", "executive"]:
            return True
        
        # Check if user has management role on this project
        from app.models.domain.document_references import ProjectAssignment
        assignment = await ProjectAssignment.find_one(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.project.id == project.id,
            ProjectAssignment.active == True
        )
        
        if assignment:
            management_roles = ["Lead", "Manager", "Director", "Technical Lead", "Project Manager"]
            return assignment.role_in_project in management_roles
        
        return False
    
    @staticmethod
    async def can_user_assign_role(assigner: InternalStakeholder, assignee: Optional[InternalStakeholder], role: str) -> bool:
        """Check if user can assign a specific role to another user"""
        assigner_seniority = AccessControlService.SENIORITY_HIERARCHY.get(assigner.seniority_level, 0)
        
        # If assignee is provided, check seniority hierarchy
        if assignee:
            assignee_seniority = AccessControlService.SENIORITY_HIERARCHY.get(assignee.seniority_level, 0)
            # Can't assign roles to people more senior than you
            if assignee_seniority >= assigner_seniority:
                return False
        
        # Role-specific restrictions
        restricted_roles = {
            "Lead": 3,  # Need to be at least lead level
            "Manager": 4,  # Need to be at least manager level
            "Director": 5,  # Need to be at least director level
        }
        
        required_level = restricted_roles.get(role, 1)
        return assigner_seniority >= required_level
    
    @staticmethod
    async def get_accessible_clients(user: InternalStakeholder) -> List[Client]:
        """Get all clients the user can access"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Executives and directors can see all clients
        if "view_everything" in permissions or "view_all_projects" in permissions:
            return await Client.find().to_list()
        
        accessible_clients = []
        
        # Get clients from specific access list
        if user.access_level and user.access_level.can_view_clients:
            for client_id in user.access_level.can_view_clients:
                try:
                    client = await Client.get(client_id)
                    if client:
                        accessible_clients.append(client)
                except:
                    continue
        
        # Get clients from project assignments
        from app.models.domain.document_references import ProjectAssignment
        assignments = await ProjectAssignment.find(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.active == True
        ).to_list()
        
        for assignment in assignments:
            project = await assignment.project.fetch()
            if project:
                client = await project.client.fetch()
                if client and client not in accessible_clients:
                    accessible_clients.append(client)
        
        return accessible_clients
    
    @staticmethod
    async def get_accessible_projects(user: InternalStakeholder) -> List[Project]:
        """Get all projects the user can access"""
        permissions = await AccessControlService.get_user_permissions(user)
        
        # Executives and directors can see all projects
        if "view_everything" in permissions or "view_all_projects" in permissions:
            return await Project.find().to_list()
        
        accessible_projects = []
        
        # Managers can see department projects
        if "view_all_department_projects" in permissions:
            from app.models.domain.document_references import ProjectAssignment
            all_assignments = await ProjectAssignment.find(
                ProjectAssignment.active == True
            ).to_list()
            
            for assignment in all_assignments:
                team_member = await assignment.internal_stakeholder.fetch()
                if team_member and hasattr(team_member, 'department') and team_member.department == user.department:
                    project = await assignment.project.fetch()
                    if project and project not in accessible_projects:
                        accessible_projects.append(project)
        
        # Get projects from direct assignments
        from app.models.domain.document_references import ProjectAssignment
        assignments = await ProjectAssignment.find(
            ProjectAssignment.internal_stakeholder.id == user.id,
            ProjectAssignment.active == True
        ).to_list()
        
        for assignment in assignments:
            project = await assignment.project.fetch()
            if project and project not in accessible_projects:
                accessible_projects.append(project)
        
        return accessible_projects
    
    @staticmethod
    async def filter_sensitive_data(user: InternalStakeholder, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data based on user's access level"""
        permissions = await AccessControlService.get_user_permissions(user)
        data_access_level = user.access_level.data_access_level if user.access_level else "basic"
        
        # Executives see everything
        if "view_everything" in permissions:
            return data
        
        filtered_data = data.copy()
        
        # Remove sensitive fields based on access level
        if data_access_level == "basic":
            sensitive_fields = ["financial_data", "strategic_plans", "salary_info", "personal_data"]
            for field in sensitive_fields:
                filtered_data.pop(field, None)
        
        elif data_access_level == "detailed":
            sensitive_fields = ["strategic_plans", "salary_info", "personal_data"]
            for field in sensitive_fields:
                filtered_data.pop(field, None)
        
        elif data_access_level == "sensitive":
            sensitive_fields = ["salary_info", "personal_data"]
            for field in sensitive_fields:
                filtered_data.pop(field, None)
        
        # Executive level sees everything (no filtering)
        
        return filtered_data

# Global instance
access_control = AccessControlService()