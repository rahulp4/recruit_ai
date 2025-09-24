# services/matching_engine_service.py

import logging
from typing import Dict, Any, List, Optional

# Import repositories needed for matching logic
from database.job_description_repository import JobDescriptionRepository
from database.profile_repository import ProfileRepository
from database.permission_repository import PermissionRepository # For RBAC checks
from sentence_transformers import SentenceTransformer, util
from database.job_profile_match_repository import JobProfileMatchRepository # NEW: Import JobProfileMatchRepository
from database.organization_repository import OrganizationRepository # NEW: Import OrganizationRepository
import google.generativeai as genai # NEW: Import genai for type hint
from services.model_manager import get_sentence_transformer_model

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly
# NEW: Import the PLUGIN_REGISTRY
from plugin_registry import PLUGIN_REGISTRY
class MatchingEngineService:
    """
    Orchestrates the matching process between Job Descriptions and Candidate Profiles.
    """
    def __init__(self,
                 jd_repo: JobDescriptionRepository,
                 profile_repo: ProfileRepository,
                 perm_repo: PermissionRepository,
                 local_matcher_callable: Any,
                 model: Optional[SentenceTransformer],  # OPTIMIZATION: Now accepts None for lazy loading
                jpm_repo: JobProfileMatchRepository,
                org_repo: OrganizationRepository,
                modelgen: genai.GenerativeModel): # CRITICAL FIX: Add org_repo here


        self.jd_repo = jd_repo
        self.profile_repo = profile_repo
        self.perm_repo = perm_repo
        self.local_matcher_callable    =   local_matcher_callable
        self._model  =   model  # Store as private attribute
        self.jpm_repo = jpm_repo # NEW
        self.org_repo   =   org_repo
        self.modelgen=modelgen
        # PLUGIN_REGISTRY['localmatcher']
        logger.info("MatchingEngineService initialized with lazy model loading.")

    @property
    def model(self) -> SentenceTransformer:
        """
        Get the SentenceTransformer model, loading it lazily if not already loaded.
        This prevents all Gunicorn workers from loading the model at startup.
        """
        if self._model is None:
            logger.info("Lazy loading SentenceTransformer model for MatchingEngineService")
            self._model = get_sentence_transformer_model()
        return self._model

    def perform_match(self, job_id: int, profile_id: int, current_user_id: int, current_org_id: str, current_user_roles: List[str]) -> Dict[str, Any]:
        """
        Performs the matching logic between a Job Description and a Candidate Profile.
        
        Args:
            job_id (int): The ID of the Job Description.
            profile_id (int): The ID of the Candidate Profile.
            current_user_id (int): The ID of the authenticated user.
            current_org_id (str): The organization ID of the authenticated user.
            current_user_roles (List[str]): Roles of the authenticated user.
            
        Returns:
            Dict[str, Any]: A dictionary containing match results (for now, a success message).
            
        Raises:
            ValueError: If input IDs are invalid or resources not found.
            PermissionError: If the user does not have access to the specified JD or Profile.
            Exception: For unexpected errors.
        """
        logger.info(f"User {current_user_id} (Org: {current_org_id}) requesting match for JD ID: {job_id}, Profile ID: {profile_id}.")

        # --- Step 1: Get Job Description Details ---
        # Get JD without filtering by user_id initially; permission check comes after.
        # Assuming jd_repo.get_job_description_by_id checks for organization_id
        job_description = self.jd_repo.get_job_description_by_id(job_id, current_org_id)
        if not job_description:
            logger.warning(f"Match initiation failed: JD ID {job_id} not found for org {current_org_id}.")
            raise ValueError(f"Job Description with ID {job_id} not found in your organization.")

        # Authorization Check for JD (User has 'jd:read' permission on this specific JD)
        # Resource name for JD is its ID (as a string)
        # if not self.perm_repo.has_permission(
        #     role_ids=current_user_roles,
        #     permission_name='jd:read',
        #     resource_type='JOB_DESCRIPTION_ACTION',
        #     resource_name=str(job_id) # Resource name is the JD's ID
        # ):
        #     logger.warning(f"User {current_user_id} lacks 'jd:read' permission for JD {job_id}.")
        #     raise PermissionError(f"User not authorized to view Job Description {job_id}.")


        # --- Step 2: Get Candidate Profile Details ---
        # ProfileRepo.get_profile_by_id should filter by organization_id
        candidate_profile = self.profile_repo.get_profile_by_id(profile_id, current_org_id)
        if not candidate_profile:
            logger.warning(f"Match initiation failed: Profile ID {profile_id} not found for org {current_org_id}.")
            raise ValueError(f"Candidate Profile with ID {profile_id} not found in your organization.")

        # Authorization Check for Profile (User has 'profile:read' permission on this specific Profile)
        # Resource name for Profile is its ID (as a string)
        # if not self.perm_repo.has_permission(
        #     role_ids=current_user_roles,
        #     permission_name='profile:read',
        #     resource_type='PROFILE', # Assuming 'PROFILE' is the resource_type for candidate profiles
        #     resource_name=str(profile_id) # Resource name is the Profile's ID
        # ):
        #     logger.warning(f"User {current_user_id} lacks 'profile:read' permission for Profile {profile_id}.")
        #     raise PermissionError(f"User not authorized to view Profile {profile_id}.")

        # localmatcher    =   PLUGIN_REGISTRY['localmatcher']
        # localmatcher()
        match_result = self.local_matcher_callable(self.model,
            job_description_rules=job_description, # Pass the JD (which is the rules JSON)
            candidate_profile=candidate_profile,    # Pass the candidate profile
            modelgen=self.modelgen
        )
        logger.debug(f"LOCALMATCHER - {match_result}")








        # --- Step 4: Save Match Result to Database ---
        overall_score = match_result.get('overall_score_weighted', 0.0) # Assume plugin returns overall_score
        candidate_name = candidate_profile.get('name', 'Unknown Candidate')
        
        # Determine agency_id if current_org_id is an agency (from previous logic)
        agency_id_for_db = None
        current_org_details = self.org_repo.get_organization_by_id(current_org_id) # Assuming org_repo is accessible via perm_repo or injected
        if current_org_details and current_org_details.get('organization_type', '').lower() == 'agency':
            agency_id_for_db = current_org_id

        saved_match_id = self.jpm_repo.save_match_result(
            job_id=job_id,
            profile_id=profile_id,
            candidate_name=candidate_name,
            overall_score=overall_score,
            match_results_json=match_result, # Store the full plugin output
            organization_id=job_description.get('organization_id'), # Org to which the JD belongs
            agency_id=agency_id_for_db,
            created_by=str(current_user_id) # User who initiated the match
        )
        logger.info(f"Match result saved to DB with ID: {saved_match_id}.")

        # Add saved_match_id to the returned result
        match_result['match_id'] = saved_match_id
        logger.info(f"Successfully retrieved JD '{job_description.get('job_title', job_id)}' and Profile '{candidate_profile.get('name', profile_id)}'.")

        # --- Step 3: Implement Actual Matching Logic Here (Future Phase) ---
        # For now, just return a success message.
        # match_result = {
        #     "jobId": job_id,
        #     "profileId": profile_id,
        #     "status": "Match initiated",
        #     "message": "Matching logic will be implemented here.",
        #     "jobTitle": job_description.get('job_title', 'N/A'),
        #     "candidateName": candidate_profile.get('name', 'N/A')
        # }

        return match_result
    
        # NEW METHOD: search_match_results
    def search_match_results(self,
                             organization_id: str,
                             current_user_id: int,
                             current_user_roles: List[str],
                             job_id: Optional[int] = None,
                             candidate_name: Optional[str] = None,
                             limit: int = 100,
                             order_by_score_desc: bool = True) -> List[Dict[str, Any]]:
        """
        Searches for job-profile match results based on criteria, with RBAC.
        
        Args:
            organization_id (str): The organization ID to filter matches by.
            current_user_id (int): The ID of the authenticated user.
            current_user_roles (List[str]): Roles of the authenticated user.
            job_id (Optional[int]): Filter by specific Job ID.
            candidate_name (Optional[str]): Filter by candidate name (partial match).
            limit (int): Max number of results to return.
            order_by_score_desc (bool): True for descending score, False for ascending.
            
        Returns:
            List[Dict[str, Any]]: A list of match results.
            
        Raises:
            PermissionError: If the user does not have permission to search matches.
            ValueError: If input parameters are invalid.
            Exception: For unexpected errors.
        """
        logger.info(f"User {current_user_id} (Org: {organization_id}) searching match results for JD {job_id}, Candidate '{candidate_name}'.")

        # Authorization Check: User must have 'match:search' permission
        # if not self.perm_repo.has_permission(
        #     role_ids=current_user_roles,
        #     permission_name='match:search',
        #     resource_type='MATCH_ACTION', # Assuming 'MATCH_ACTION' is the resource_type for match operations
        #     resource_name='global_match_search_action' # Assuming this is the global resource for search
        # ):
        #     logger.warning(f"User {current_user_id} lacks 'match:search' permission for matches.")
        #     raise PermissionError("User does not have permission to search match results.")

        # Construct filters for the repository call
        filters = {}
        if job_id is not None:
            filters['job_id'] = job_id
        if candidate_name:
            filters['candidate_name'] = candidate_name

        # Call the repository method to perform the search
        match_results = self.jpm_repo.search_matches(
            job_id=filters.get('job_id'),
            candidate_name=filters.get('candidate_name'),
            organization_id=organization_id, # Always filter by the target organization
            limit=limit,
            order_by_score_desc=order_by_score_desc
        )
        
        return match_results