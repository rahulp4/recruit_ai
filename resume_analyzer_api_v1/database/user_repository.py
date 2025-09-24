# database/user_repository.py

import logging
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class UserRepository:
    """
    Data Access Layer for User entities.
    """
    def __init__(self):
        logger.info("UserRepository initialized.")

    def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user by their Firebase UID."""
        session = get_db_session()
        try:
            query = text("SELECT id, firebase_uid, email, organization_id, is_active FROM users WHERE firebase_uid = :firebase_uid;")
            result = session.execute(query, {'firebase_uid': firebase_uid}).fetchone()
            if result:
                return {
                    "id": result.id,
                    "firebase_uid": result.firebase_uid,
                    "email": result.email,
                    "organization_id": result.organization_id,
                    "is_active": result.is_active
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by Firebase UID {firebase_uid}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_user_roles(self, user_id: int) -> List[str]:
        """
        Retrieves a list of role names for a given user ID.
        Updated to use roles.roleId (VARCHAR) as primary key.
        """
        session = get_db_session()
        try:
            query = text("""
                SELECT r.name
                FROM roles r
                JOIN user_roles ur ON r.roleId = ur.role_id -- CRITICAL CHANGE: Join on roleId
                WHERE ur.user_id = :user_id;
            """)
            results = session.execute(query, {'user_id': user_id}).fetchall()
            roles = [row.name for row in results]
            logger.debug(f"Retrieved roles {roles} for user ID {user_id}.")
            return roles
        except Exception as e:
            logger.error(f"Error getting roles for user ID {user_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def add_user(self, firebase_uid: str, email: str, organization_id: str, is_active: bool = True) -> int:
        """Adds a new user to the database."""
        session = get_db_session()
        try:
            query = text("""
                INSERT INTO users (firebase_uid, email, organization_id, is_active)
                VALUES (:firebase_uid, :email, :organization_id, :is_active)
                ON CONFLICT (firebase_uid) DO UPDATE SET email = EXCLUDED.email, organization_id = EXCLUDED.organization_id, is_active = EXCLUDED.is_active
                RETURNING id;
            """)
            result = session.execute(query, {
                'firebase_uid': firebase_uid,
                'email': email,
                'organization_id': organization_id,
                'is_active': is_active
            })
            session.commit()
            logger.info(f"User '{email}' ({firebase_uid}) added/updated successfully.")
            return result.scalar_one()
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding user {firebase_uid}: {e}", exc_info=True)
            raise
        finally:
            session.close()
            
    def assign_role_to_user(self, user_id: int, role_id: str, assigned_by: str) -> bool: # NEW METHOD
        """
        Assigns a role to a user.
        Args:
            user_id (int): The internal database ID of the user.
            role_id (str): The ID of the role (e.g., 'RECRUITER', 'ADMIN').
            assigned_by (str): The identifier of the user/system assigning the role.
        Returns:
            bool: True if role assigned, False if already assigned.
        """
        session = get_db_session()
        try:
            query = text("""
                INSERT INTO user_roles (user_id, role_id, created_by)
                VALUES (:user_id, :role_id, :created_by)
                ON CONFLICT (user_id, role_id) DO NOTHING;
            """)
            result = session.execute(query, {
                'user_id': user_id,
                'role_id': role_id,
                'created_by': assigned_by
            })
            session.commit()
            is_assigned = result.rowcount > 0
            if is_assigned:
                logger.info(f"Role '{role_id}' assigned to user ID {user_id} by {assigned_by}.")
            else:
                logger.info(f"Role '{role_id}' already assigned to user ID {user_id}.")
            return is_assigned
        except Exception as e:
            session.rollback()
            logger.error(f"Error assigning role '{role_id}' to user {user_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()            