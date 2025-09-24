# database/organization_repository.py

import logging
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class OrganizationRepository:
    """
    Data Access Layer for Organization entities.
    """
    def __init__(self):
        logger.info("OrganizationRepository initialized.")

    def get_organizations_by_ids(self, org_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves details for a list of specific organization IDs.
        Handles the psycopg2 malformed array literal error for ANY operator.
        """
        if not org_ids:
            return []

        session = get_db_session()
        try:
            # CRITICAL FIX: Explicitly cast the parameter to TEXT[] (array of text)
            # PostgreSQL requires array literals to start with '{' or dimension info.
            # SQLAlchemy/psycopg2 sometimes passes ('val1', 'val2') for ANY, which can be misparsed.
            # Explicitly casting ensures it's treated as an array.
            query = text("""
                SELECT id, name, organization_type, is_active, created_by, created_at
                FROM organizations
                WHERE id = ANY(CAST(:org_ids AS TEXT[])) AND is_active = TRUE -- CRITICAL FIX HERE
                ORDER BY name ASC;
            """)
            
            # The parameter needs to be a list or tuple. SQLAlchemy will handle conversion.
            results = session.execute(query, {'org_ids': org_ids}).fetchall() # Pass as list (or tuple)

            orgs = []
            for row in results:
                orgs.append({
                    "id": row.id,
                    "name": row.name,
                    "organizationType": row.organization_type,
                    "isActive": row.is_active,
                    "createdBy": row.created_by,
                    "createdAt": row.created_at.isoformat()
                })
            logger.info(f"Retrieved {len(orgs)} organizations by ID list.")
            return orgs
        except Exception as e:
            logger.error(f"Error retrieving organizations by IDs {org_ids}: {e}", exc_info=True)
            raise
        finally:
            session.close()

            
    def get_organization_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an organization by its ID, including new fields.
        """
        session = get_db_session()
        try:
            query = text("SELECT id, name, organization_type, is_active, created_by FROM organizations WHERE id = :org_id;")
            result = session.execute(query, {'org_id': org_id}).fetchone()
            if result:
                return {
                    "id": result.id,
                    "name": result.name,
                    "organization_type": result.organization_type,
                    "is_active": result.is_active,
                    "created_by": result.created_by
                }
            return None
        except Exception as e:
            logger.error(f"Error getting organization by ID {org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def add_organization(self, org_id: str, name: str, organization_type: Optional[str] = None, is_active: bool = True, created_by: Optional[str] = None) -> str:
        """
        Adds a new organization to the database, including organization_type and created_by.
        Updates existing organization if ID conflicts.
        """
        session = get_db_session()
        try:
            query = text("""
                INSERT INTO organizations (id, name, organization_type, is_active, created_by)
                VALUES (:id, :name, :organization_type, :is_active, :created_by)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    organization_type = EXCLUDED.organization_type,
                    is_active = EXCLUDED.is_active,
                    created_by = EXCLUDED.created_by,
                    created_at = EXCLUDED.created_at -- Ensure created_at is not updated on conflict if already set
                RETURNING id;
            """)
            result = session.execute(query, {
                'id': org_id,
                'name': name,
                'organization_type': organization_type,
                'is_active': is_active,
                'created_by': created_by
            })
            session.commit()
            logger.info(f"Organization '{name}' ({org_id}) added/updated successfully with type '{organization_type}'.")
            return result.scalar_one()
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding organization {org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def update_organization(self, org_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates specific fields for an existing organization.
        Args:
            org_id (str): The ID of the organization to update.
            updates (Dict[str, Any]): A dictionary of fields to update (e.g., {'name': 'New Name', 'is_active': False}).
        Returns:
            bool: True if updated, False if org_id not found.
        """
        if not updates:
            logger.info(f"No updates provided for organization {org_id}.")
            return False

        session = get_db_session()
        try:
            set_clauses = []
            params = {'org_id': org_id}
            
            allowed_updates = ['name', 'organization_type', 'is_active', 'created_by'] # List of updatable fields

            for key, value in updates.items():
                if key in allowed_updates:
                    set_clauses.append(f"{key} = :{key}")
                    params[key] = value
                else:
                    logger.warning(f"Attempted to update non-updatable field: {key} for organization {org_id}.")

            if not set_clauses:
                logger.info(f"No valid updatable fields found in updates for organization {org_id}.")
                return False

            set_clause_str = ", ".join(set_clauses)
            query = text(f"""
                UPDATE organizations
                SET {set_clause_str}, updated_at = CURRENT_TIMESTAMP
                WHERE id = :org_id;
            """)
            
            result = session.execute(query, params)
            session.commit()
            is_updated = result.rowcount > 0
            logger.info(f"Organization {org_id} updated: {is_updated}. Fields updated: {updates.keys()}")
            return is_updated
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating organization {org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def list_organizations(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of organizations, optionally filtered.
        Filters can include 'is_active', 'organization_type', 'name_like'.
        """
        session = get_db_session()
        try:
            where_clauses = []
            params = {}

            if filters:
                if 'is_active' in filters and filters['is_active'] is not None:
                    where_clauses.append("is_active = :is_active")
                    params['is_active'] = filters['is_active']
                if 'organization_type' in filters and filters['organization_type']:
                    where_clauses.append("organization_type = :organization_type")
                    params['organization_type'] = filters['organization_type']
                if 'name_like' in filters and filters['name_like']:
                    where_clauses.append("name ILIKE :name_like")
                    params['name_like'] = f"%{filters['name_like']}%"

            sql_query = "SELECT id, name, organization_type, is_active, created_by, created_at FROM organizations"
            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)
            sql_query += " ORDER BY created_at DESC;"

            results = session.execute(text(sql_query), params).fetchall()

            orgs = []
            for row in results:
                orgs.append({
                    "id": row.id,
                    "name": row.name,
                    "organizationType": row.organization_type,
                    "isActive": row.is_active,
                    "createdBy": row.created_by,
                    "createdAt": row.created_at.isoformat() # Convert datetime to ISO format
                })
            logger.info(f"Retrieved {len(orgs)} organizations with filters {filters}.")
            return orgs
        except Exception as e:
            logger.error(f"Error listing organizations with filters {filters}: {e}", exc_info=True)
            raise
        finally:
            session.close()