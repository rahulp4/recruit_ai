# database/agency_info_repository.py

import logging
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

class AgencyInfoRepository:
    """
    Data Access Layer for agency_info table.
    Manages affiliations between agency organizations and their client organizations.
    """
    def __init__(self):
        logger.info("AgencyInfoRepository initialized.")

    def get_affiliated_organizations(self, agency_org_id: str) -> List[str]:
        """
        Retrieves a list of orgId strings that are affiliated with the given agencyOrgId.
        """
        session = get_db_session()
        try:
            query = text("""
                SELECT orgId FROM agency_info
                WHERE agencyOrgId = :agency_org_id;
            """)
            results = session.execute(query, {'agency_org_id': agency_org_id}).fetchall()
            affiliated_org_ids = [row.orgid for row in results] # Access row.orgid (lowercase)
            logger.debug(f"Retrieved {len(affiliated_org_ids)} affiliations for agency {agency_org_id}.")
            return affiliated_org_ids
        except Exception as e:
            logger.error(f"Error getting affiliations for agency {agency_org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def add_affiliation(self, agency_org_id: str, client_org_id: str, created_by: str) -> bool:
        """
        Adds a new affiliation between an agency and a client organization.
        """
        session = get_db_session()
        try:
            query = text("""
                INSERT INTO agency_info (agencyOrgId, orgId, created_by)
                VALUES (:agency_org_id, :client_org_id, :created_by)
                ON CONFLICT (agencyOrgId, orgId) DO NOTHING; -- Prevents duplicate entries
            """)
            result = session.execute(query, {
                'agency_org_id': agency_org_id,
                'client_org_id': client_org_id,
                'created_by': created_by
            })
            session.commit()
            is_added = result.rowcount > 0
            if is_added:
                logger.info(f"Affiliation added: Agency {agency_org_id} -> Client {client_org_id}.")
            else:
                logger.info(f"Affiliation already exists: Agency {agency_org_id} -> Client {client_org_id}.")
            return is_added
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding affiliation {agency_org_id} -> {client_org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_agency_for_client_org(self, client_org_id: str) -> Optional[str]:
        """
        Retrieves the agency organization ID for a given client organization ID.
        Returns the first one found if multiple exist.
        """
        session = get_db_session()
        try:
            query = text("""
                SELECT agencyOrgId FROM agency_info
                WHERE orgId = :client_org_id LIMIT 1;
            """)
            result = session.execute(query, {'client_org_id': client_org_id}).scalar_one_or_none()
            if result:
                logger.debug(f"Found agency '{result}' for client org '{client_org_id}'.")
            return result
        except Exception as e:
            logger.error(f"Error getting agency for client org {client_org_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()