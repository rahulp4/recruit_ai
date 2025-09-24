# services/resource_service.py

import logging
from typing import List, Dict, Any, Optional

from database.resource_repository import ResourceRepository

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class ResourceService:
    """
    Business logic for managing application resources, e.g., menu items.
    """
    def __init__(self, resource_repository: ResourceRepository):
        self.resource_repository = resource_repository
        logger.info("ResourceService initialized.")

    def get_menu_items(self, organization_id: Optional[str] = None, user_roles: Optional[List[str]] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]: # Added user_id
        """
        Retrieves and formats menu items relevant to a specific organization or global ones.
        Filters menu items based on user's roles and associated permissions.
        
        Args:
            organization_id (Optional[str]): The ID of the organization to filter menus by.
            user_roles (Optional[List[str]]): List of role IDs (e.g., 'ADMIN', 'RECRUITER') for the authenticated user.
            user_id (Optional[int]): The internal database user ID (crucial for get_resources_by_type).
        Returns:
            List[Dict[str, Any]]: A list of formatted menu items that the user has permission to view.
        """
        if user_roles is None:
            user_roles = [] # Ensure it's a list for safety
        if user_id is None:
            logger.warning("get_menu_items called without user_id. Cannot perform RBAC filtering.")
            return [] # Cannot fetch user-specific menus without user_id

        # Step 1: Get all raw menu items relevant to the organization AND accessible by the user's roles
        # This calls the method in ResourceRepository that uses the complex SQL query
        raw_menu_items = self.resource_repository.get_resources_by_type( # CRITICAL FIX: Call resource_repository
            resource_type="MENU", 
            organization_id=organization_id,
            user_id=user_id # Pass user_id to the repository method
        )
        
        # At this point, raw_menu_items should already be filtered by user, roles, and orgId by the SQL query.
        # No further Python-side filtering for 'has_permission' needed on this list if the SQL is correct.
        
        # Step 2: Format the menu items
        formatted_menu = []
        for item in raw_menu_items:
            formatted_menu.append({
                "id": item['id'],
                "name": item['name'],
                "displayName": item['displayName'],
                "path": item['path'],
                "icon": item['icon'],
                "parentId": item['parentId'],
                "orderIndex": item['orderIndex'],
                "orgId": item['orgId']
            })
        
        # Step 3: Sort for consistent hierarchy building in UI (parent_id then order_index)
        formatted_menu.sort(key=lambda x: (x['parentId'] if x['parentId'] is not None else -1, x['orderIndex']))

        logger.info(f"Returning {len(formatted_menu)} filtered menu items for org '{organization_id if organization_id else 'global'}' for user {user_id} with roles {user_roles}.")
        return formatted_menu