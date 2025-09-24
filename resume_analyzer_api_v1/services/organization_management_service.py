# services/organization_management_service.py

import logging
from typing import Dict, Any, Optional, List
from database.organization_repository import OrganizationRepository
from database.permission_repository import PermissionRepository # For RBAC checks
from database.agency_info_repository import AgencyInfoRepository # NEW: Import AgencyInfoRepository

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class OrganizationManagementService:
    """
    Business logic for managing Organization entities.
    Handles creation, retrieval, updating, and listing of organizations with RBAC.
    """
    def __init__(self, org_repo: OrganizationRepository, perm_repo: PermissionRepository,agency_info_repo:AgencyInfoRepository ):
        self.org_repo = org_repo
        self.perm_repo = perm_repo
        self.agency_info_repo   =    agency_info_repo
        logger.info("OrganizationManagementService initialized.")

    def create_organization(self, org_id: str, name: str, organization_type: Optional[str], current_user_id: int, current_user_roles: List[str]) -> Dict[str, Any]:
        """
        Creates a new organization.
        Requires 'org:create' permission on the 'global_org_create_action' resource.
        """
        # Authorization Check: User must have 'org:create' permission
        if not self.perm_repo.has_permission(
            role_ids=current_user_roles,
            permission_name='org:create',
            resource_type='ORGANIZATION_ACTION', # Type of the resource for global actions
            resource_name='global_org_create_action' # Specific resource name for this action
        ):
            logger.warning(f"User {current_user_id} with roles {current_user_roles} attempted to create org but lacks 'org:create' permission.")
            raise PermissionError("User does not have permission to create organizations.")
        
        # Get user email/id from DB to store as 'created_by' (optional, if you want email, else use user_id)
        # Assuming user_id is enough or you fetch user_email from UserRepository if needed.
        created_by_identifier = str(current_user_id) # Using internal DB ID for created_by

        # Validate input data (basic, can be enhanced with Pydantic for input validation)
        if not org_id or not name:
            raise ValueError("Organization ID and Name are required.")

        # Call repository to add the organization
        new_org_id = self.org_repo.add_organization(
            org_id=org_id,
            name=name,
            organization_type=organization_type,
            is_active=True,
            created_by=created_by_identifier
        )
        logger.info(f"Organization '{name}' created by user {current_user_id}.")
        
        # Return newly created organization details (fetch them back if needed, or rely on input)
        return self.org_repo.get_organization_by_id(new_org_id) # Fetch full details

    def list_accessible_organizations(self, current_user_id: int, current_org_id: str, current_user_roles: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves a list of organizations accessible to the current user's organization.
        - If user's organization is of type 'Agency', returns agency's own org + all affiliated client orgs.
        - If user's organization is not an 'Agency', returns only their own organization's details.
        Requires 'org:list_accessible' permission.
        """
        # Authorization Check: User must have 'org:list_accessible' permission
        # if not self.perm_repo.has_permission(
        #     role_ids=current_user_roles,
        #     permission_name='org:list_accessible', # A new permission you need to define
        #     resource_type='ORGANIZATION_ACTION',
        #     resource_name='global_accessible_org_list_action' # A new specific resource name
        # ):
        #     logger.warning(f"User {current_user_id} lacks 'org:list_accessible' permission.")
        #     raise PermissionError("User does not have permission to list accessible organizations.")
        
        # Get current organization's type
        current_org_details = self.org_repo.get_organization_by_id(current_org_id)
        if not current_org_details:
            logger.error(f"Current user's organization {current_org_id} not found in DB.")
            raise ValueError("Current user's organization not found.")
        
        accessible_org_ids = [current_org_id] # An organization can always access itself
        
        if current_org_details.get('organization_type', '').lower() == 'agency':
            # If it's an agency, get all affiliated client organizations
            logger.debug(f"Org type is agency {current_org_id}")
            affiliated_client_org_ids = self.agency_info_repo.get_affiliated_organizations(current_org_id)
            logger.debug(f"Org type affiliated_client_org_ids {affiliated_client_org_ids}")
            accessible_org_ids.extend(affiliated_client_org_ids)
            # Remove duplicates just in case
            accessible_org_ids = list(set(accessible_org_ids)) 
            logger.info(f"Agency {current_org_id} has access to {len(affiliated_client_org_ids)} affiliated clients.")
        else:
            logger.info(f"Organization {current_org_id} is not an agency. Returning only its own details.")

        # Retrieve full details for all accessible organizations
        # Assumes get_organizations_by_ids handles filtering by is_active=TRUE internally.
        accessible_org_details = self.org_repo.get_organizations_by_ids(accessible_org_ids)
        
        return accessible_org_details

    def get_organization(self, org_id: str, current_user_id: int, current_org_id: str, current_user_roles: List[str]) -> Optional[Dict[str, Any]]:
        """
        Retrieves details of a specific organization.
        Requires 'org:read' permission on the specific org_id OR global 'org:list' for admins.
        """
        # Authorization Check:
        # User must have 'org:read' permission for THIS specific organization (org_id)
        # OR, if they are an ADMIN, they might have 'org:list' permission globally (if implemented)
        # or 'org:read' on a general org resource.
        # For simplicity, if they belong to this org, they can read. Admins can read any.

        # Policy: A user can read their own organization's details OR have global read permissions.
        if current_org_id != org_id:
             # If they are not in the requested org, they need org:read permission on THAT specific org_id
             # OR, a global list permission (org:list) if it implies seeing all orgs.
             if not self.perm_repo.has_permission(
                role_ids=current_user_roles,
                permission_name='org:read',
                resource_type='ORGANIZATION_ACTION', # assuming specific org is an action
                resource_name=org_id # Resource is the specific organization itself
             ) and not self.perm_repo.has_permission( # Also check for org:list if ADMIN can see all
                role_ids=current_user_roles,
                permission_name='org:list', # Or a general 'org:read_all' permission
                resource_type='ORGANIZATION_ACTION',
                resource_name='global_org_list_action' # The specific resource for listing all orgs
             ):
                 logger.warning(f"User {current_user_id} lacks 'org:read' permission for org {org_id} and is not in that org.")
                 raise PermissionError(f"User not authorized to view organization {org_id}.")
        # If current_org_id == org_id, user implicitly has permission (or org:read on their own org).

        return self.org_repo.get_organization_by_id(org_id)

    def update_organization(self, org_id: str, updates: Dict[str, Any], current_user_id: int, current_org_id: str, current_user_roles: List[str]) -> bool:
        """
        Updates an existing organization.
        Requires 'org:update' permission on the specific org_id.
        """
        # Authorization Check: User must have 'org:update' permission for THIS specific organization
        if not self.perm_repo.has_permission(
            role_ids=current_user_roles,
            permission_name='org:update',
            resource_type='ORGANIZATION_ACTION',
            resource_name=org_id # Resource is the specific organization itself
        ):
            logger.warning(f"User {current_user_id} lacks 'org:update' permission for org {org_id}.")
            raise PermissionError(f"User not authorized to update organization {org_id}.")
        
        # If trying to modify active status, requires ADMIN role (example policy)
        if 'is_active' in updates and not ('ADMIN' in current_user_roles): # Or check a more specific 'org:activate' permission
            logger.warning(f"User {current_user_id} (roles {current_user_roles}) attempted to change 'is_active' for org {org_id} without ADMIN role.")
            raise PermissionError("Only Admins can change organization active status.")

        return self.org_repo.update_organization(org_id, updates)

    def list_organizations(self, filters: Optional[Dict[str, Any]], current_user_id: int, current_user_roles: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves a list of organizations based on filters.
        Requires 'org:list' permission (often tied to a global resource).
        """
        # Authorization Check: User must have 'org:list' permission (global permission)
        if not self.perm_repo.has_permission(
            role_ids=current_user_roles,
            permission_name='org:list',
            resource_type='ORGANIZATION_ACTION',
            resource_name='global_org_list_action' # The specific resource for listing all orgs
        ):
            logger.warning(f"User {current_user_id} lacks 'org:list' permission.")
            raise PermissionError("User does not have permission to list organizations.")
        
        return self.org_repo.list_organizations(filters)