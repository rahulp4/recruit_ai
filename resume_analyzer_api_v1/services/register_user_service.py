# services/register_user_service.py

import logging
import uuid 
from typing import Dict, Any, List, Optional
# Removed direct import of firebase_admin.auth here if AuthService handles it.
# from firebase_admin import auth 

from database.organization_repository import OrganizationRepository
from database.user_repository import UserRepository
from database.permission_repository import PermissionRepository
from auth.auth_service import AuthService # To verify firebase ID token (its own method)

logger = logging.getLogger(__name__)

class RegisterUserService:
    """
    Handles the registration of new users and their association with organizations.
    """
    def __init__(self,
                 org_repo: OrganizationRepository,
                 user_repo: UserRepository,
                 perm_repo: PermissionRepository,
                 auth_service: AuthService): # Inject AuthService for token verification
        self.org_repo = org_repo
        self.user_repo = user_repo
        self.perm_repo = perm_repo
        self.auth_service = auth_service
        logger.info("RegisterUserService initialized.")

    def register_new_user(self, full_name: str, organization_name: str, email: str, firebase_id_token: str, organization_id: str) -> Dict[str, Any]: # CRITICAL FIX: Add organization_id
           """
           Registers a new user, creates/associates an organization, and assigns a default role.
           """
           logger.info(f"Attempting to register new user: '{email}' for organization: '{organization_name}' (ID: {organization_id}).")

           # 1. Verify Firebase ID Token
           try:
               decoded_token = self.auth_service.verify_firebase_id_token_and_get_user_info(firebase_id_token) 
               firebase_uid = decoded_token['uid']
               if decoded_token.get('email') != email:
                   logger.warning(f"Firebase token email mismatch: Token={decoded_token.get('email')}, Provided={email}")
                   raise ValueError("Firebase token email does not match provided email.")
           except Exception as e:
               logger.error(f"Firebase ID token verification failed during registration: {e}", exc_info=True)
               raise ValueError(f"Invalid Firebase ID Token: {str(e)}")

           # 2. Check/Create Organization using the provided organization_id
           # Try to get the organization by the provided ID
           organization_info = self.org_repo.get_organization_by_id(organization_id)
           
           if organization_info:
               # Organization exists, confirm name matches (optional check)
               if organization_info['name'] != organization_name:
                   logger.warning(f"Provided organization_name '{organization_name}' does not match existing org ID '{organization_id}' with name '{organization_info['name']}'. Using existing org's name.")
                   # You might raise an error here if strict name matching is required.
               logger.info(f"Organization '{organization_name}' (ID: {organization_id}) already exists.")
           else:
               # Organization does not exist, create it with the provided ID
               try:
                   self.org_repo.add_organization(
                       org_id=organization_id, # Use the provided ID
                       name=organization_name,
                       organization_type='OWN', # Default type for new orgs
                       is_active=True,
                       created_by=email # User's email as creator
                   )
                   logger.info(f"New organization '{organization_name}' created with ID: {organization_id}.")
               except Exception as e:
                   logger.error(f"Failed to create new organization '{organization_name}' with ID '{organization_id}': {e}", exc_info=True)
                   raise RuntimeError(f"Failed to create organization: {str(e)}")

           # 3. Check/Create User
           user_info = self.user_repo.get_user_by_firebase_uid(firebase_uid)
           if user_info:
               logger.info(f"User '{email}' ({firebase_uid}) already exists with ID: {user_info['id']}.")
               user_db_id = user_info['id']
               # If user exists but is tied to a different organization, decide policy:
               # - Allow re-association (update user's organization_id)
               # - Deny registration (raise error)
               # For now, we'll log a warning if mismatch and assume user stays with original org.
               if user_info['organization_id'] != organization_id:
                   logger.warning(f"User {email} exists but associated with different org '{user_info['organization_id']}'. Will NOT change user's organization to '{organization_id}'.")
                   # If you want to update the user's organization, you'd need an update_user method here.
                   # For this flow, we assume a user is permanently tied to their first registered org.
           else:
               try:
                   user_db_id = self.user_repo.add_user(
                       firebase_uid=firebase_uid,
                       email=email,
                       organization_id=organization_id, # Use the provided organization_id
                       is_active=True
                   )
                   logger.info(f"New user '{email}' created with DB ID: {user_db_id}.")
               except Exception as e:
                   logger.error(f"Failed to create new user '{email}': {e}", exc_info=True)
                   raise RuntimeError(f"Failed to create user: {str(e)}")

           # 4. Assign Default Role to User
           default_role_id = 'RECRUITER' 
           try:
               self.user_repo.assign_role_to_user(user_db_id, default_role_id, assigned_by='system_registration')
               logger.info(f"Default role '{default_role_id}' assigned to user {email}.")
           except Exception as e:
               logger.error(f"Failed to assign default role to user {email}: {e}", exc_info=True)

           logger.info(f"User '{email}' successfully registered and associated with org '{organization_name}' (ID: {organization_id}).")
           return {"status": "success", "message": "User registered successfully.", "user_id": user_db_id, "organization_id": organization_id}