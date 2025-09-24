# auth/auth_service.py

import logging
import jwt
import datetime
from firebase_admin import auth 
from typing import Dict, Any, List, Optional

from database.organization_repository import OrganizationRepository
from database.user_repository import UserRepository
from auth.firebase_manager import verify_firebase_id_token
from database.agency_info_repository import AgencyInfoRepository

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class AuthService:
    def __init__(self, org_repo: OrganizationRepository, user_repo: UserRepository, agency_info_repo: AgencyInfoRepository, app_secret_key: str):
        self.org_repo = org_repo
        self.user_repo = user_repo
        self.agency_info_repo = agency_info_repo
        self.app_secret_key = app_secret_key
        if not self.app_secret_key or self.app_secret_key == 'your_super_secret_flask_key_change_me_in_production':
            logger.warning("APP_SECRET_KEY is not set or is default. Please change it in production!")
        logger.info("AuthService initialized.")

    def authenticate_and_authorize(self, organization_id: str, firebase_id_token: str) -> Dict[str, Any]:
        """
        Authenticates user via Firebase token and authorizes against organization.
        Returns a dictionary including custom session token, user details, and roles.
        The organizationId is validated but not returned explicitly as it's an input.
        """
        org_info = self.org_repo.get_organization_by_id(organization_id)
        if not org_info:
            logger.warning(f"Authentication failed: Invalid Organization ID {organization_id}")
            raise ValueError("Invalid Organization ID")
        if not org_info.get('is_active'):
            logger.warning(f"Authentication failed: Organization {organization_id} is inactive.")
            raise ValueError("Organization is inactive")

        # NEW: Get organization type from the fetched organization info
        organization_type = org_info.get('organization_type')

        # NEW: Check if this org is a client of an agency
        agency_org_id = self.agency_info_repo.get_agency_for_client_org(organization_id)
        if agency_org_id:
            logger.info(f"Organization {organization_id} is a client of agency {agency_org_id}.")

        try:
            decoded_token = verify_firebase_id_token(firebase_id_token)
            uid = decoded_token['uid']
            user_email = decoded_token.get('email')
            logger.info(f"Firebase ID Token verified for UID: {uid}, Email: {user_email}")

        except auth.InvalidIdTokenError:
            logger.warning("Authentication failed: Invalid Firebase ID Token.")
            raise ValueError("Invalid Firebase ID Token")
        except Exception as e:
            logger.error(f"Error during Firebase ID Token verification: {e}", exc_info=True)
            raise ValueError("Authentication failed during token verification")

        user_info = self.user_repo.get_user_by_firebase_uid(uid)
        if not user_info:
            logger.warning(f"Authentication failed: User {uid} not found in local DB.")
            raise ValueError("User not registered in the system")
        
        if user_info.get('organization_id') != organization_id:
            logger.warning(f"Authorization failed: User {uid} not associated with organization {organization_id}.")
            raise ValueError("User not authorized for this organization")
        
        if not user_info.get('is_active'):
            logger.warning(f"Authorization failed: User {uid} is inactive.")
            raise ValueError("User account is inactive")

        # --- Authentication and Authorization Successful! ---
        internal_user_id = user_info['id']
        user_roles = self.user_repo.get_user_roles(internal_user_id)

        # Generate custom backend session token
        # Embed crucial info like user_id, org_id, and roles into the session token
        session_token = self._generate_session_token(uid, organization_id, internal_user_id, user_roles, organization_type, agency_org_id)
        logger.info(f"Login successful for UID: {uid} in Org: {organization_id}")

        # Streamlined return: return user-specific data and session token.
        # organizationId is *not* returned as it was an input parameter to the route already.
        return {
            "sessionToken": session_token,
            "uid": uid,
            "userId": internal_user_id,
            "email": user_email,
            "roles": user_roles,
            "organizationType": organization_type,
            "agencyOrgId": agency_org_id
        }

    def _generate_session_token(self, uid: str, organization_id: str, internal_user_id: int, roles: List[str], organization_type: Optional[str], agency_org_id: Optional[str], expires_in_hours: int = 12) -> str:
        """Generates a custom JWT session token."""
        try:
            session_payload = {
                "uid": uid,
                "userId": internal_user_id,
                "organizationId": organization_id, # Still include in token for decorator's g.organization_id
                "organizationType": organization_type, # NEW: Add organization type to token payload
                "parentOrgId": agency_org_id, # NEW: Add agency org id as parentOrgId
                "roles": roles,                  
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
            }
            token = jwt.encode(session_payload, self.app_secret_key, algorithm="HS256")
            return token
        except Exception as e:
            logger.error(f"Error generating session token for UID {uid}: {e}", exc_info=True)
            raise ValueError("Internal server error during session creation")

    def get_user_from_session_token(self, session_token: str) -> Dict[str, Any]:
        """Decodes and validates the custom session token."""
        try:
            payload = jwt.decode(session_token, self.app_secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired.")
            raise ValueError("Session token expired")
        except jwt.InvalidTokenError:
            logger.warning("Invalid session token.")
            raise ValueError("Invalid session token")
        except Exception as e:
            logger.error(f"Error decoding session token: {e}", exc_info=True)
            raise ValueError("Session token decoding failed")
        
        
    # NEW METHOD: Dedicated for Firebase ID Token verification
    def verify_firebase_id_token_and_get_user_info(self, firebase_id_token: str) -> Dict[str, Any]:
        """
        Verifies a Firebase ID token using firebase_admin SDK.
        This is separate from verifying our custom session tokens.
        """
        try:
            decoded_token = auth.verify_id_token(firebase_id_token)
            logger.info(f"Firebase ID Token verified by SDK for UID: {decoded_token['uid']}")
            return decoded_token
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Firebase SDK: Invalid ID Token: {e}")
            raise ValueError(f"Invalid Firebase ID Token: {e}")
        except Exception as e:
            logger.error(f"Firebase SDK: Error verifying ID Token: {e}", exc_info=True)
            raise ValueError(f"Firebase ID Token verification failed: {e}")        