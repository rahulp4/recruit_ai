# database/permission_repository.py

import logging
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class PermissionRepository:
    """
    Data Access Layer for Permission entities.
    """
    def __init__(self):
        logger.info("PermissionRepository initialized.")

    def get_role_permissions(self, role_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all permissions (by permission name and associated resource) for a given role.
        """
        session = get_db_session()
        try:
            query = text("""
                SELECT
                    p.name AS permission_name,
                    p.resource_type AS permission_resource_type,
                    rp.resource_id AS permission_resource_id
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = :role_id;
            """)
            results = session.execute(query, {'role_id': role_id}).fetchall()
            
            permissions = []
            for row in results:
                permissions.append({
                    "name": row.permission_name,
                    "resourceType": row.permission_resource_type,
                    "resourceId": row.permission_resource_id # Will be NULL for global
                })
            logger.debug(f"Retrieved {len(permissions)} permissions for role '{role_id}'.")
            return permissions
        except Exception as e:
            logger.error(f"Error getting permissions for role '{role_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()

    def has_permission(self, role_ids: List[str], permission_name: str, resource_type: str, resource_id: Optional[int] = None) -> bool:
        """
        Checks if any of the given roles has the specified permission for a resource.
        A role has permission if:
        1. It has the permission for the specific resource_id.
        2. OR, it has the permission globally for that resource_type (resource_id IS NULL).
        """
        if not role_ids:
            return False
            
        session = get_db_session()
        try:
            # This query checks for both specific resource permission AND global resource_type permission
            query_str = """
                SELECT EXISTS (
                    SELECT 1
                    FROM role_permissions rp
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE rp.role_id IN :role_ids
                      AND p.name = :permission_name
                      AND p.resource_type = :resource_type
                      AND (rp.resource_id = :resource_id OR rp.resource_id IS NULL)
                    LIMIT 1
                );
            """
            # If resource_id is None, it only checks for the global (rp.resource_id IS NULL) part.
            # If resource_id is not None, it checks for both specific AND global.
            
            # This needs to be carefully handled for resource_id IS NULL matching specific resource_id
            # The simpler approach is to check if global for resource_type OR specific for resource_id
            
            # Let's adjust the query for clarity:
            query_str = """
                SELECT EXISTS (
                    SELECT 1
                    FROM role_permissions rp
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE rp.role_id = ANY(:role_ids) -- Use ANY for list of role_ids
                      AND p.name = :permission_name
                      AND p.resource_type = :resource_type
                      AND (rp.resource_id IS NULL OR rp.resource_id = :resource_id)
                    LIMIT 1
                );
            """

            params = {
                'role_ids': tuple(role_ids), # SQLAlchemy needs tuple for IN/ANY
                'permission_name': permission_name,
                'resource_type': resource_type,
                'resource_id': resource_id # Pass None if no specific resource
            }

            result = session.execute(text(query_str), params).scalar_one()
            
            logger.debug(f"Permission check for roles {role_ids} on {permission_name} for resource {resource_type}:{resource_id} resulted in {result}.")
            return result # Returns True or False
        except Exception as e:
            logger.error(f"Error checking permission for roles {role_ids} on {permission_name} for resource {resource_type}:{resource_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()