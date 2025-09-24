# database/resource_repository.py

import logging
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class ResourceRepository:
    """
    Data Access Layer for Resource entities (like menu items, permissions).
    """
    def __init__(self):
        logger.info("ResourceRepository initialized.")

    def get_resources_by_type1(self, resource_type: str, organization_id: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of resources filtered by type and optionally by organization_id and user_id.
        This method implements the full RBAC query for menus accessible by a specific user.
        """
        session = get_db_session()
        try:
            if user_id is None: 
                logger.warning("Attempted to get menu items without user_id. Returning empty list.")
                return []

            sql_query = """
            SELECT
                r.id,
                r.name,
                r.display_name,
                r.path,
                r.icon,
                r.parent_id,
                r.order_index,
                r.orgid,
                r.is_active
            FROM
                resources r
            JOIN
                role_permissions rp ON rp.resource_id = r.id     
            JOIN
                permissions p ON rp.permission_id = p.id         
            JOIN
                user_roles ur ON ur.role_id = rp.roleid          
            JOIN
                users u ON u.id = ur.user_id                     
            WHERE
                u.id = :user_id_param                            
                AND p.name = :permission_name_filter             
                AND r.resource_type = :resource_type_filter      
                AND r.is_active = TRUE                           
                AND (
                    r.orgid IS NULL                              
                    OR r.orgid = u.organization_id               
                )
            ORDER BY
                r.parent_id NULLS FIRST, r.order_index ASC;
            """
            
            params = {
                'user_id_param': user_id,
                'permission_name_filter': 'execute', # Default permission for menu viewing
                'resource_type_filter': resource_type # e.g., 'MENU'
            }

            # logger.debug(f"Executing SQL query for menu items:\n{sql_query}\nWith params: {params}")
            results = session.execute(text(sql_query), params).fetchall()
            
            resources = []
            for row in results:
                resources.append({
                    "id": row.id,
                    "resourceType": resource_type, # Use input param for consistency
                    "name": row.name,
                    "displayName": row.display_name,
                    "path": row.path,
                    "icon": row.icon,
                    "parentId": row.parent_id,
                    "orderIndex": row.order_index,
                    "isActive": row.is_active,
                    "orgId": row.orgid # Access by attribute
                })
            # logger.info(f"Retrieved {len(resources)} resources of type '{resource_type}' for user {user_id} in org '{organization_id if organization_id else 'global'}'.")
            return resources
        except Exception as e:
            logger.error(f"Error getting resources by type '{resource_type}' for user {user_id} in org '{organization_id if organization_id else 'global'}': {e}", exc_info=True)
            raise
        finally:
            session.close()
            

    def get_resources_by_type(self, resource_type: str, organization_id: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of resources filtered by type and optionally by organization_id and user_id.
        This method implements the full RBAC query for menus accessible by a specific user.
        """
        session = get_db_session()
        try:
            if user_id is None: 
                logger.warning("Attempted to get menu items without user_id. Returning empty list.")
                return []

            sql_query = """
            SELECT
                r.id,
                r.name,
                r.display_name,
                r.path,
                r.icon,
                r.parent_id,
                r.order_index,
                r.orgid,
                r.is_active
            FROM
                resources r
            JOIN
                role_permissions rp ON rp.resource_id = r.id     
            JOIN
                permissions p ON rp.permission_id = p.id         
            JOIN
                user_roles ur ON ur.role_id = rp.roleid          
            JOIN
                users u ON u.id = ur.user_id                     
            WHERE
                u.id = :user_id_param                            
                AND p.name = :permission_name_filter             
                AND r.resource_type = :resource_type_filter      
                AND r.is_active = TRUE                           
            ORDER BY
                r.order_index ASC;
            """
            # r.parent_id NULLS FIRST, r.order_index ASC;
            params = {
                'user_id_param': user_id,
                'permission_name_filter': 'execute', # Default permission for menu viewing
                'resource_type_filter': resource_type # e.g., 'MENU'
            }

            # logger.debug(f"Executing SQL query for menu items:\n{sql_query}\nWith params: {params}")
            results = session.execute(text(sql_query), params).fetchall()
            
            resources = []
            for row in results:
                resources.append({
                    "id": row.id,
                    "resourceType": resource_type, # Use input param for consistency
                    "name": row.name,
                    "displayName": row.display_name,
                    "path": row.path,
                    "icon": row.icon,
                    "parentId": row.parent_id,
                    "orderIndex": row.order_index,
                    "isActive": row.is_active,
                    "orgId": row.orgid # Access by attribute
                })
            # logger.info(f"Retrieved {len(resources)} resources of type '{resource_type}' for user {user_id} in org '{organization_id if organization_id else 'global'}'.")
            return resources
        except Exception as e:
            logger.error(f"Error getting resources by type '{resource_type}' for user {user_id} in org '{organization_id if organization_id else 'global'}': {e}", exc_info=True)
            raise
        finally:
            session.close()            

    def get_resources_by_typev1(self, resource_type: str, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of resources filtered by type and optionally by organization_id.
        If organization_id is provided, it retrieves resources global to all (orgId IS NULL)
        and resources specific to that organization.
        """
        session = get_db_session()
        try:
            where_clauses = ["resource_type = :resource_type", "is_active = TRUE"]
            params = {'resource_type': resource_type}

            if organization_id:
                where_clauses.append("(orgid IS NULL OR orgid = :organization_id)") # CRITICAL FIX: Use orgid
                params['organization_id'] = organization_id
            else:
                where_clauses.append("orgid IS NULL") # CRITICAL FIX: Use orgid

            query = text(f"""
                SELECT id, resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgid -- CRITICAL FIX: Use orgid (lowercase, no quotes needed, or "orgid")
                FROM resources
                WHERE {' AND '.join(where_clauses)}
                ORDER BY parent_id NULLS FIRST, order_index ASC;
            """)
            
            results = session.execute(query, params).fetchall()
            
            resources = []
            for row in results:
                resources.append({
                    "id": row.id,
                    "resourceType": row.resource_type,
                    "name": row.name,
                    "displayName": row.display_name,
                    "path": row.path,
                    "icon": row.icon,
                    "orgId": row.orgid, # CRITICAL FIX: Access by row.orgid
                    "parentId": row.parent_id,
                    "orderIndex": row.order_index,
                    "isActive": row.is_active
                })
            logger.info(f"Retrieved {len(resources)} resources of type '{resource_type}' for org '{organization_id if organization_id else 'global'}'.")
            return resources
        except Exception as e:
            logger.error(f"Error getting resources by type '{resource_type}' for org '{organization_id if organization_id else 'global'}': {e}", exc_info=True)
            raise
        finally:
            session.close()


    def add_resource(self, resource_type: str, name: str, display_name: str, path: Optional[str] = None, icon: Optional[str] = None, parent_id: Optional[int] = None, order_index: Optional[int] = None, is_active: bool = True, org_id: Optional[str] = None) -> int:
        """
        Adds a new resource to the database, including orgId.
        Updates existing resource if name conflicts.
        """
        session = get_db_session()
        try:
            query = text("""
                INSERT INTO resources (resource_type, name, display_name, path, icon, parent_id, order_index, is_active, orgid) -- CRITICAL FIX: Use orgid here too
                VALUES (:resource_type, :name, :display_name, :path, :icon, :parent_id, :order_index, :is_active, :org_id)
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    path = EXCLUDED.path,
                    icon = EXCLUDED.icon,
                    parent_id = EXCLUDED.parent_id,
                    order_index = EXCLUDED.order_index,
                    is_active = EXCLUDED.is_active,
                    orgid = EXCLUDED.orgid, -- CRITICAL FIX: Use orgid here too
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """)
            result = session.execute(query, {
                'resource_type': resource_type, 'name': name, 'display_name': display_name,
                'path': path, 'icon': icon, 'parent_id': parent_id,
                'order_index': order_index, 'is_active': is_active, 'org_id': org_id
            })
            session.commit()
            resource_id = result.scalar_one()
            logger.info(f"Resource '{name}' (ID: {resource_id}, Org: {org_id if org_id else 'Global'}) added/updated successfully.")
            return resource_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding resource '{name}' (Org: {org_id if org_id else 'Global'}): {e}", exc_info=True)
            raise
        finally:
            session.close()