# services/job_description_management_service.py

import logging
import io
from typing import Dict, Any, Optional, List, Union # Added Union for type hinting

from services.jd_parser_service import JDParserService
from services.embedding_service import EmbeddingService
from database.job_description_repository import JobDescriptionRepository
from services.document_processor import DocumentProcessor 

from database.organization_repository import OrganizationRepository 
from database.permission_repository import PermissionRepository 

# from models.job_description_models import JobDescription, JobTitleRule, LocationRule, EmploymentTypeRule, AboutUsRule, PositionSummaryRule, KeyResponsibilitiesRule, RequiredQualificationsRule, PreferredQualificationsRule, DegreeRule, FieldOfStudyRule, OrganizationSwitchesRule, CurrentTitleRule # Import rule models for type checking
from models.job_description_models import JobDescription, BaseRuleConfig, JobTitleRule, LocationRule, EmploymentTypeRule, AboutUsRule, PositionSummaryRule, KeyResponsibilitiesRule, RequiredQualificationsRule, PreferredQualificationsRule, DegreeRule, FieldOfStudyRule, OrganizationSwitchesRule, CurrentTitleRule # CRITICAL FIX: Include BaseRuleConfig

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) 

# CRITICAL FIX: Define _get_rule_data_safe as a global helper function
def _get_rule_data_safe(parsed_jd_obj: JobDescription, rule_attr_name: str) -> Optional[Union[str, List[str]]]:
    """Safely retrieves the 'data' attribute from an optional rule object within JobDescription."""
    rule_obj = getattr(parsed_jd_obj, rule_attr_name, None) # Safely get the rule object
    if rule_obj and rule_obj.data is not None: # Check if object exists AND its data is not None
        return rule_obj.data
    return None

class JobDescriptionManagementService:
    def __init__(self,
                 jd_parser_service: JDParserService,
                 embedding_service: EmbeddingService,
                 jd_repository: JobDescriptionRepository,
                 org_repo: OrganizationRepository, 
                 perm_repo: PermissionRepository):
        
        self.jd_parser_service = jd_parser_service
        self.embedding_service = embedding_service
        self.jd_repository = jd_repository
        self.org_repo = org_repo 
        self.perm_repo = perm_repo 
        logger.info("JobDescriptionManagementService initialized.")
        
    def process_uploaded_jd(self,
                               jd_file_stream: io.BytesIO,
                               user_id: int,
                               organization_id: str, 
                               file_name: Optional[str] = "unknown_jd.docx",
                               current_user_org_id: Optional[str] = None, 
                               current_user_roles: Optional[List[str]] = None,
                               user_tags: Optional[List[str]] = None, 
                               is_active: bool = True,
                               jd_version: Optional[int] = 1,
                               jd_organization_type: Optional[str] = None,
                               parent_org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes an uploaded Job Description file.
        1. Extracts text.
        2. Parses JD into structured JSON (JobMatchingRules).
        3. Generates embedding.
        4. Stores user-defined tags and active/version status.
        5. Stores in database.
        """
        logger.info(f"Processing JD '{file_name}' for target org {organization_id} by user {user_id} (Actual org: {current_user_org_id}, Parent/Agency Org: {parent_org_id}, Version: {jd_version}).")

        # Authorization Check for Uploading JD for a Target Organization
        # if current_user_org_id != organization_id:
            # if not self.perm_repo.has_permission(
            #     role_ids=current_user_roles,
            #     permission_name='org:upload_jd_for_other', 
            #     resource_type='ORGANIZATION_ACTION',
            #     resource_name='global_upload_jd_action'
            # ):
            #     logger.warning(f"User {user_id} from org {current_user_org_id} attempted to upload JD for {organization_id} but lacks permission.")
            #     raise PermissionError(f"User not authorized to upload JD for organization {organization_id}.")

        try:
            # If the organization type was not provided from the context (because target_org != user's_org),
            # we must fetch it from the database to ensure correctness.
            if jd_organization_type is None:
                logger.info(f"Organization type not available from context for target org {organization_id}. Fetching from DB.")
                organization_details = self.org_repo.get_organization_by_id(organization_id)
                if organization_details:
                    jd_organization_type = organization_details.get('organization_type')


            # 1. Parse JD into structured JSON (returns JobMatchingRules object)
            jd_file_stream.seek(0) 
            parsed_jd_rules_obj: JobDescription = self.jd_parser_service.parse_job_description(jd_file_stream)
            logger.info(f"JD parsing successful. Extracted rules: {parsed_jd_rules_obj.model_dump_json(indent=2)[:500]}...")
            
            # Add user-defined tags and is_active status to the Pydantic object
            if user_tags is not None:
                parsed_jd_rules_obj.user_tags = user_tags
            parsed_jd_rules_obj.is_active = is_active 
            parsed_jd_rules_obj.jd_version = jd_version 
            
            # 2. Generate Embedding for Semantic Search
            text_for_embedding_parts = []

            # Use the global helper function _get_rule_data_safe
            job_title_data = _get_rule_data_safe(parsed_jd_rules_obj, 'job_title')
            if job_title_data:
                if isinstance(job_title_data, list): text_for_embedding_parts.extend(job_title_data)
                elif isinstance(job_title_data, str): text_for_embedding_parts.append(job_title_data)

            location_data = _get_rule_data_safe(parsed_jd_rules_obj, 'location')
            if location_data:
                if isinstance(location_data, list): text_for_embedding_parts.extend(location_data)
                elif isinstance(location_data, str): text_for_embedding_parts.append(location_data)

            employment_type_data = _get_rule_data_safe(parsed_jd_rules_obj, 'employment_type')
            if employment_type_data:
                if isinstance(employment_type_data, list): text_for_embedding_parts.extend(employment_type_data)
                elif isinstance(employment_type_data, str): text_for_embedding_parts.append(employment_type_data)
            
            about_us_data = _get_rule_data_safe(parsed_jd_rules_obj, 'about_us')
            if about_us_data: text_for_embedding_parts.append(about_us_data)

            position_summary_data = _get_rule_data_safe(parsed_jd_rules_obj, 'position_summary')
            if position_summary_data: text_for_embedding_parts.append(position_summary_data)
            
            key_responsibilities_data = _get_rule_data_safe(parsed_jd_rules_obj, 'key_responsibilities')
            if key_responsibilities_data: text_for_embedding_parts.append(key_responsibilities_data)
            
            required_qualifications_data = _get_rule_data_safe(parsed_jd_rules_obj, 'required_qualifications')
            if required_qualifications_data: text_for_embedding_parts.append(required_qualifications_data)
            
            preferred_qualifications_data = _get_rule_data_safe(parsed_jd_rules_obj, 'preferred_qualifications')
            if preferred_qualifications_data: text_for_embedding_parts.append(preferred_qualifications_data)
            
            what_we_offer_data = _get_rule_data_safe(parsed_jd_rules_obj, 'what_we_offer')
            if what_we_offer_data: 
                if isinstance(what_we_offer_data, list): text_for_embedding_parts.extend(what_we_offer_data)
                elif isinstance(what_we_offer_data, str): text_for_embedding_parts.append(what_we_offer_data)
            
            to_apply_data = _get_rule_data_safe(parsed_jd_rules_obj, 'to_apply')
            if to_apply_data: text_for_embedding_parts.append(to_apply_data)
            
            equal_opportunity_employer_statement_data = _get_rule_data_safe(parsed_jd_rules_obj, 'equal_opportunity_employer_statement')
            if equal_opportunity_employer_statement_data: text_for_embedding_parts.append(equal_opportunity_employer_statement_data)

            degree_data = _get_rule_data_safe(parsed_jd_rules_obj, 'degree')
            if degree_data:
                if isinstance(degree_data, list): text_for_embedding_parts.extend(degree_data)
                elif isinstance(degree_data, str): text_for_embedding_parts.append(degree_data)

            field_of_study_data = _get_rule_data_safe(parsed_jd_rules_obj, 'field_of_study')
            if field_of_study_data:
                if isinstance(field_of_study_data, list): text_for_embedding_parts.extend(field_of_study_data)
                elif isinstance(field_of_study_data, str): text_for_embedding_parts.append(field_of_study_data)

            organization_switches_data = _get_rule_data_safe(parsed_jd_rules_obj, 'organization_switches')
            if organization_switches_data: text_for_embedding_parts.append(organization_switches_data)

            current_title_data = _get_rule_data_safe(parsed_jd_rules_obj, 'current_title')
            if current_title_data:
                if isinstance(current_title_data, list): text_for_embedding_parts.extend(current_title_data)
                elif isinstance(current_title_data, str): text_for_embedding_parts.append(current_title_data)

            text_for_embedding = " ".join(filter(None, text_for_embedding_parts)).strip()
            logger.debug(f"Text for embedding (first 200 chars): {text_for_embedding[:200]}")
            
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            
            # if embedding:
            #     parsed_jd_rules_obj.embedding = embedding 
            # else:
            #     job_title_for_log = _get_rule_data_safe(parsed_jd_rules_obj, 'job_title') 
            #     if isinstance(job_title_for_log, list): job_title_for_log = " ".join(job_title_for_log)
            #     logger.warning(f"Failed to generate embedding for JD: {job_title_for_log if job_title_for_log else 'Unknown JD'}")
            #     parsed_jd_rules_obj.embedding = None 

            # Add user_id and organization_id to the Pydantic object
            parsed_jd_rules_obj.user_id = user_id
            parsed_jd_rules_obj.organization_id = organization_id

            # Store in PostgreSQL
            jd_db_id = self.jd_repository.save_job_description(
                jd_data=parsed_jd_rules_obj, 
                embedding=embedding, 
                user_id=user_id,
                organization_id=organization_id,
                jd_organization_type=jd_organization_type, # Pass the determined organization type
                parent_org_id=parent_org_id # NEW: Pass parent org id
            )
            logger.info(f"Job Description saved with ID: {jd_db_id} for user {user_id} in org {organization_id}.")

            parsed_jd_rules_obj.db_id = jd_db_id

            return parsed_jd_rules_obj.model_dump(by_alias=True)

        except ValueError as ve:
            logger.error(f"JD parsing or data validation error: {ve}", exc_info=True)
            raise 
        except Exception as e:
            logger.error(f"An unexpected error occurred during JD processing: {e}", exc_info=True)
            raise         
    def process_uploaded_jdv2(self,
                               jd_file_stream: io.BytesIO,
                               user_id: int,
                               organization_id: str, 
                               file_name: Optional[str] = "unknown_jd.docx",
                               current_user_org_id: Optional[str] = None, 
                               current_user_roles: Optional[List[str]] = None,
                               user_tags: Optional[List[str]] = None, 
                               is_active: bool = True,
                               jd_version: Optional[int] = 1) -> Dict[str, Any]:
        """
        Processes an uploaded Job Description file.
        1. Extracts text.
        2. Parses JD into structured JSON (JobMatchingRules).
        3. Generates embedding.
        4. Stores user-defined tags and active/version status.
        5. Stores in database.
        """
        logger.info(f"Processing JD '{file_name}' for target org {organization_id} by user {user_id} (Actual org: {current_user_org_id}, Version: {jd_version}).")

        # Authorization Check for Uploading JD for a Target Organization
        if current_user_org_id != organization_id:
            if not self.perm_repo.has_permission(
                role_ids=current_user_roles,
                permission_name='org:upload_jd_for_other', 
                resource_type='ORGANIZATION_ACTION',
                resource_name='global_upload_jd_action'
            ):
                logger.warning(f"User {user_id} from org {current_user_org_id} attempted to upload JD for {organization_id} but lacks permission.")
                raise PermissionError(f"User not authorized to upload JD for organization {organization_id}.")

        try:
            # 1. Parse JD into structured JSON (returns JobMatchingRules object)
            jd_file_stream.seek(0) 
            parsed_jd_rules_obj: JobDescription = self.jd_parser_service.parse_job_description(jd_file_stream)
            logger.info(f"JD parsing successful. Extracted rules: {parsed_jd_rules_obj.model_dump_json(indent=2)[:500]}...")
            
            # Add user-defined tags and is_active status to the Pydantic object
            if user_tags is not None:
                parsed_jd_rules_obj.user_tags = user_tags
            parsed_jd_rules_obj.is_active = is_active 
            parsed_jd_rules_obj.jd_version = jd_version 
            
            # 2. Generate Embedding for Semantic Search
            text_for_embedding_parts = []

            # CRITICAL FIX: Use getattr(obj, 'attr', None) or access via model_dump for safety
            # This handles cases where the LLM might entirely omit an optional rule field.

            # Helper to extract data from optional rule objects and add to parts
            def add_rule_data_to_embedding_parts(rule_attr_name: str):
                rule_obj = getattr(parsed_jd_rules_obj, rule_attr_name, None) # Safely get the rule object
                if rule_obj and rule_obj.data is not None: # Check if object exists AND its data is not None
                    if isinstance(rule_obj.data, list):
                        text_for_embedding_parts.extend(rule_obj.data)
                    elif isinstance(rule_obj.data, str):
                        text_for_embedding_parts.append(rule_obj.data)
            
            # Apply helper to all optional rule fields
            add_rule_data_to_embedding_parts('job_title')
            add_rule_data_to_embedding_parts('location')
            add_rule_data_to_embedding_parts('employment_type')
            add_rule_data_to_embedding_parts('about_us')
            add_rule_data_to_embedding_parts('position_summary')
            add_rule_data_to_embedding_parts('key_responsibilities')
            add_rule_data_to_embedding_parts('required_qualifications')
            add_rule_data_to_embedding_parts('preferred_qualifications')
            add_rule_data_to_embedding_parts('what_we_offer')
            add_rule_data_to_embedding_parts('to_apply')
            add_rule_data_to_embedding_parts('equal_opportunity_employer_statement')
            add_rule_data_to_embedding_parts('degree')
            add_rule_data_to_embedding_parts('field_of_study')
            add_rule_data_to_embedding_parts('organization_switches')
            add_rule_data_to_embedding_parts('current_title')

            # Handle keywordmatch (also optional at top level)
            # if parsed_jd_rules_obj.keywordmatch:
            #     if parsed_jd_rules_obj.keywordmatch.technical_skills:
            #         text_for_embedding_parts.extend(parsed_jd_rules_obj.keywordmatch.technical_skills)
            #     if parsed_jd_rules_obj.keywordmatch.soft_skills:
            #         text_for_embedding_parts.extend(parsed_jd_rules_obj.keywordmatch.soft_skills)
            #     if parsed_jd_rules_obj.keywordmatch.certifications:
            #         text_for_embedding_parts.extend(parsed_jd_rules_obj.keywordmatch.certifications)


            text_for_embedding = " ".join(filter(None, text_for_embedding_parts)).strip()
            logger.debug(f"Text for embedding (first 200 chars): {text_for_embedding[:200]}")
            
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            
            if embedding:
                parsed_jd_rules_obj.embedding = embedding 
            else:
                # Log a more specific name if job_title data is available
                job_title_for_log = get_rule_data(parsed_jd_rules_obj.job_title) # Use helper function
                if isinstance(job_title_for_log, list): job_title_for_log = " ".join(job_title_for_log)
                logger.warning(f"Failed to generate embedding for JD: {job_title_for_log if job_title_for_log else 'Unknown JD'}")
                parsed_jd_rules_obj.embedding = None 

            # Add user_id and organization_id to the Pydantic object
            parsed_jd_rules_obj.user_id = user_id
            parsed_jd_rules_obj.organization_id = organization_id

            # 3. Store in PostgreSQL
            jd_db_id = self.jd_repository.save_job_description(
                jd_data=parsed_jd_rules_obj, 
                embedding=embedding, 
                user_id=user_id,
                organization_id=organization_id
            )
            logger.info(f"Job Description saved with ID: {jd_db_id} for user {user_id} in org {organization_id}.")

            parsed_jd_rules_obj.db_id = jd_db_id

            return parsed_jd_rules_obj.model_dump(by_alias=True)

        except ValueError as ve:
            logger.error(f"JD parsing or data validation error: {ve}", exc_info=True)
            raise 
        except Exception as e:
            logger.error(f"An unexpected error occurred during JD processing: {e}", exc_info=True)
            raise 
    def process_uploaded_jdv1(self,
                            jd_file_stream: io.BytesIO,
                            user_id: int,
                            organization_id: str, 
                            file_name: Optional[str] = "unknown_jd.docx",
                            current_user_org_id: Optional[str] = None, 
                            current_user_roles: Optional[List[str]] = None,
                            user_tags: Optional[List[str]] = None, 
                            is_active: bool = True,
                            jd_version: Optional[int] = 1) -> Dict[str, Any]: # NEW: jd_version parameter
        """
        Processes an uploaded Job Description file.
        1. Extracts text.
        2. Parses JD into structured JSON.
        3. Generates embedding.
        4. Stores user-defined tags and active/version status.
        5. Stores in database.
        """
        logger.info(f"Processing JD '{file_name}' for target org {organization_id} by user {user_id} (Actual org: {current_user_org_id}, Version: {jd_version}).")

        # Authorization Check for Uploading JD for a Target Organization
        if current_user_org_id != organization_id:
            if not self.perm_repo.has_permission(
                role_ids=current_user_roles,
                permission_name='org:upload_jd_for_other', 
                resource_type='ORGANIZATION_ACTION',
                resource_name='global_upload_jd_action'
            ):
                logger.warning(f"User {user_id} from org {current_user_org_id} attempted to upload JD for {organization_id} but lacks permission.")
                raise PermissionError(f"User not authorized to upload JD for organization {organization_id}.")

        try:
            # 1. Parse JD into structured JSON
            jd_file_stream.seek(0) 
            parsed_jd_obj: JobDescription = self.jd_parser_service.parse_job_description(jd_file_stream)
            logger.info(f"JD parsing successful for title: {parsed_jd_obj.job_title}.")
            
            # NEW: Add user-defined tags and is_active status to the Pydantic object
            if user_tags is not None:
                parsed_jd_obj.user_tags = user_tags
            parsed_jd_obj.is_active = is_active 
            parsed_jd_obj.jd_version = jd_version # NEW: Set JD version
            
            # 2. Generate Embedding for Semantic Search
            text_for_embedding = f"{parsed_jd_obj.job_title} {parsed_jd_obj.position_summary} {' '.join(parsed_jd_obj.key_responsibilities)} {' '.join(parsed_jd_obj.required_qualifications)} {' '.join(parsed_jd_obj.preferred_qualifications)} {' '.join(parsed_jd_obj.what_we_offer)}"
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            
            # if embedding:
            #     parsed_jd_obj.embedding = embedding
            # else:
            #     logger.warning(f"Failed to generate embedding for JD: {parsed_jd_obj.job_title}")
            #     parsed_jd_obj.embedding = None 

            # Add user_id and organization_id to the Pydantic object
            parsed_jd_obj.user_id = user_id
            parsed_jd_obj.organization_id = organization_id

            # 3. Store in PostgreSQL
            jd_db_id = self.jd_repository.save_job_description(
                jd_data=parsed_jd_obj,
                embedding=embedding,
                user_id=user_id,
                organization_id=organization_id
            )
            logger.info(f"Job Description '{parsed_jd_obj.job_title}' stored successfully with DB ID: {jd_db_id}")

            parsed_jd_obj.db_id = jd_db_id

            return parsed_jd_obj.model_dump(by_alias=True)

        except ValueError as ve:
            logger.error(f"JD parsing or data validation error: {ve}", exc_info=True)
            raise 
        except Exception as e:
            logger.error(f"An unexpected error occurred during JD processing: {e}", exc_info=True)
            raise 
 
 
    def get_job_descriptions_for_organization(self, organization_id: str, current_user_id: int, current_user_roles: List[str], include_inactive: bool = False, user_tag: Optional[str] = None, jd_version: Optional[int] = None) -> List[Dict[str, Any]]: # NEW: jd_version
        """
        Retrieves a list of Job Descriptions accessible to a specific organization.
        Requires 'jd:read' permission. Supports filtering by active status, user tags, and jd_version.
        """
        #  if not self.perm_repo.has_permission(
        #      role_ids=current_user_roles,
        #      permission_name='jd:read',
        #      resource_type='JOB_DESCRIPTION_ACTION', 
        #      resource_name='global_jd_read_action'
        #  ):
        #      logger.warning(f"User {current_user_id} from org {organization_id} lacks 'jd:read' permission.")
        #      raise PermissionError("User does not have permission to list job descriptions.")
        
        # Build filters for the repository call
        filters = {}
        filters['is_active'] = not include_inactive
        if user_tag:
            filters['user_tag'] = user_tag
        if jd_version is not None: # NEW: Add jd_version to filters
            filters['jd_version'] = jd_version

        # Call repository to get JDs filtered by the organization ID and new filters
        jds = self.jd_repository.get_job_descriptions_by_organization(
            organization_id=organization_id,
            include_inactive=include_inactive, 
            filters=filters 
        )
        
        return jds
    def get_job_description_details(self, jd_id: int, organization_id: str, current_user_id: int, current_user_roles: List[str]) -> Optional[Dict[str, Any]]: # NEW METHOD
        """
        Retrieves details for a single Job Description by its ID.
        Requires 'jd:read' permission for the specific JD or a global 'jd:read' permission.
        """
        # Authorization Check: User must have 'jd:read' permission
        # Policy: User can read JDs belonging to their organization OR if they have a global 'jd:read' permission.
        # Also, ensure JD belongs to the org.
        
        # Get the JD first to confirm its organization_id
        jd_details = self.jd_repository.get_job_description_by_id(jd_id, organization_id)

        if not jd_details:
            logger.warning(f"JD ID {jd_id} not found for org {organization_id} or is inactive.")
            return None # Not found or not active

        # Ensure the JD belongs to the organization specified in the URL/request
        if jd_details['organizationId'] != organization_id:
            logger.warning(f"JD {jd_id} belongs to org {jd_details['organizationId']} but requested for {organization_id}. Mismatch.")
            raise PermissionError("JD not found in specified organization or access denied.")


        # Check permission for this specific JD.
        # If the user's role has 'jd:read' permission on this specific jd_id, OR
        # if they have 'jd:read' permission on a global resource for JDs.
        # Assuming 'jd:read' permission grants access to view.
        # if not self.perm_repo.has_permission(
        #     role_ids=current_user_roles,
        #     permission_name='jd:read',
        #     resource_type='JOB_DESCRIPTION_ACTION', # The resource type of the permission
        #     resource_name=str(jd_id) # Resource name is the JD's ID for specific JD permissions
        # ) and not self.perm_repo.has_permission( # Also check for global permission
        #     role_ids=current_user_roles,
        #     permission_name='jd:read',
        #     resource_type='JOB_DESCRIPTION_ACTION',
        #     resource_name='global_jd_read_action' # The specific resource for reading all JDs
        # ):
            logger.warning(f"User {current_user_id} lacks 'jd:read' permission for JD {jd_id}.")
            raise PermissionError(f"User not authorized to view Job Description {jd_id}.")
        
        return jd_details

    def get_active_jd_count_for_organization(self, organization_id: str, organization_type: str) -> int:
        """
        Gets the count of active job descriptions for an organization,
        differentiating logic for OWN vs AGENCY organization types.
        """
        logger.info(f"Getting active JD count for org: {organization_id} with type: {organization_type}")

        # Determine if we should query by parent_org_id based on the organization type.
        # If the user's organization is an 'AGENCY', we count JDs they manage via parent_org_id.
        # Otherwise, for 'OWN' or other types, we count JDs they own via organization_id.
        is_agency = organization_type and organization_type.lower() == 'agency'

        # Call the repository with the correct flag
        count = self.jd_repository.count_active_job_descriptions(
            organization_id=organization_id,
            by_parent_org=is_agency
        )
        
        return count
