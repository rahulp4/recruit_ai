# services/profile_management_service.py

import logging
import io
import json # Used for json.dumps
from typing import Dict, Any, Optional
from flask import current_app # To access services attached to current_app context

# Import services and repository that ProfileManagementService orchestrates
from services.resume_parser_service import ResumeParserService
from services.data_analyzer_service import DataAnalyzerService
from services.embedding_service import EmbeddingService
from database.profile_repository import ProfileRepository
from database.organization_repository import OrganizationRepository
from matchai import MatchAIClient # Ensure this path is correct for your MatchAIClient library
import tempfile # For temporary file handling
import os       # <--- ADD THIS IMPORT
# NEW: Import DocumentProcessor
from services.document_processor import DocumentProcessor
from services.openai_resume_parser_service import OpenAIResumeParserService
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly
from services.file_storage_service import FileStorageService # NEW: Import FileStorageService

class ProfileManagementService:
    """
    Orchestrates the end-to-end process of parsing, analyzing, embedding,
    and storing an uploaded resume profile.
    """
    def __init__(self,
                 resume_parser_service: ResumeParserService,
                 data_analyzer_service: DataAnalyzerService,
                 embedding_service: EmbeddingService,
                 profile_repository: ProfileRepository,
                 organization_repository: OrganizationRepository):
        
        self.resume_parser_service = resume_parser_service
        self.data_analyzer_service = data_analyzer_service
        self.embedding_service = embedding_service
        self.profile_repository = profile_repository
        self.org_repo = organization_repository
        
        # MatchAIClient is special: it's attached to app.match_ai_client
        # We need to access it via current_app when the method is called.
        self._match_ai_client = None 

        logger.info("ProfileManagementService initialized.")

    def set_match_ai_client(self, client_instance: Any):
        """Sets the MatchAIClient instance. Called from app.py."""
        self._match_ai_client = client_instance
        logger.info("MatchAIClient instance set in ProfileManagementService.")


    # NEW METHOD: Contains the logic from /upload-resume (V1)
    def process_uploaded_resume_v1(self, 
                                   file_stream: io.BytesIO, 
                                   user_id: int, 
                                   organization_id: str,
                                   file_name: Optional[str] = "unknown_file.docx",
                                   filebatchid: Optional[str] = None,
                                   jd_organization_type: Optional[str] = None,
                                   parent_org_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes an uploaded resume file using the V1 (our internal LLM) parsing method.
        Includes DOCX extraction, calculations, embedding, and storage.
        """
        logger.info(f"Processing resume '{file_name}' for user {user_id} in target org {organization_id} (V1 method). Parent/Agency Org: {parent_org_id}")

        try:
            # If the organization type was not provided from the context (because target_org != user's_org),
            # we must fetch it from the database to ensure correctness.
            if jd_organization_type is None:
                logger.info(f"Organization type not available from context for target org {organization_id}. Fetching from DB.")
                organization_details = self.org_repo.get_organization_by_id(organization_id)
                if organization_details:
                    jd_organization_type = organization_details.get('organization_type')

            # Initialize DocumentProcessor for the file stream
            # Ensure DocumentProcessor handles BytesIO streams correctly.
            # Assuming DocumentProcessor expects a BytesIO stream
            document_processor = DocumentProcessor(file_stream) 
            raw_resume_text = document_processor.get_combined_document_content()
            # logger.debug(f"Raw String from DocumentProcessor: {raw_resume_text[:500]}...")

            llm_parsed_data = self.resume_parser_service.parse_resume_with_gemini(raw_resume_text) 
            # open    =   OpenAIResumeParserService()
            # llm_parsed_data = open.parse_resume_with_openai(raw_resume_text)
            # --- Apply additional calculations ---
            llm_parsed_data["organization_switches"] = self.data_analyzer_service.calculate_organization_switches(
                llm_parsed_data.get("experience", [])
            )
            llm_parsed_data['technology_experience_years'] = self.data_analyzer_service.calculate_technology_experience_years(
                llm_parsed_data
            )
            llm_parsed_data['time_spent_in_org'] = self.data_analyzer_service.calculate_time_spent_in_organizations(
                llm_parsed_data.get('experience', [])
            )
            
            if 'total_experience_years' not in llm_parsed_data or llm_parsed_data['total_experience_years'] is None:
                llm_parsed_data['total_experience_years'] = self.data_analyzer_service.calculate_total_experience(
                    llm_parsed_data.get('experience', [])
                )
                logger.info(f"Calculated total_experience_years as {llm_parsed_data['total_experience_years']} (LLM did not provide explicitly).")
            else:
                logger.info(f"Using LLM-provided total_experience_years: {llm_parsed_data['total_experience_years']}.")


            llm_parsed_data['total_experience_years'] = self.data_analyzer_service.calculate_total_experience(
                llm_parsed_data.get('experience', [])
            )
            # logger.info(f"Calculated total_experience_years as {llm_parsed_data['total_experience_years']} ")




            # NEW: Calculate and add recent skills with experience (e.g., last 2 years)
            # You can make the 'recent_years' configurable if needed
            llm_parsed_data['recent_skills_overview'] = self.data_analyzer_service.get_recent_skills_with_experience(
                parsed_data=llm_parsed_data,
                recent_years=6 # Default to 2 years, make configurable if needed
            )
            logger.info(f"V1: Calculated recent skills overview for last 2 years {llm_parsed_data['recent_skills_overview']}")

            # NEW: Calculate current job tenure and populate fields
            current_company, current_title, current_tenure_years = self.data_analyzer_service.calculate_current_job_tenure(llm_parsed_data)
            llm_parsed_data['current_company'] = current_company
            llm_parsed_data['current_title'] = current_title
            llm_parsed_data['current_tenure_years'] = current_tenure_years
            logger.info(f"V1: Calculated current job details: {current_company}, {current_title}, {current_tenure_years} years.")



            text_for_embedding = self.embedding_service.build_text_for_embedding(llm_parsed_data)
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            
            # if embedding:
            #     llm_parsed_data['embedding'] = embedding
            # else:
            #     logger.warning(f"Failed to generate embedding for profile: {llm_parsed_data.get('name', 'Unknown')}")
            #     llm_parsed_data['embedding'] = None 

            # Store in PostgreSQL
            profile_id = self.profile_repository.save_profile(
                profile_data=llm_parsed_data,
                embedding=embedding,
                user_id=user_id,
                organization_id=organization_id,
                filebatchid=filebatchid,
                jd_organization_type=jd_organization_type,
                parent_org_id=parent_org_id
            )
            logger.info(f"Profile for {llm_parsed_data.get('name', 'Unknown')} stored successfully with DB ID: {profile_id}")

            llm_parsed_data['db_id'] = profile_id

            logger.info("Resume processed and stored successfully. Returning prettified JSON.")
            
            return llm_parsed_data # Return the processed dict
            
        except ValueError as ve:
            logger.error(f"V1: Data validation error: {ve}", exc_info=True)
            raise # Re-raise to be caught by route
        except Exception as e:
            logger.error(f"V1: An unexpected error occurred during resume processing: {e}", exc_info=True)
            raise # Re-raise to be caught by route

    # Existing process_uploaded_resume method (now becomes process_uploaded_resume_v2)
    def process_uploaded_resume(self, # Renamed from process_uploaded_resume_v2 internally
                                   file_stream: io.BytesIO,
                                   user_id: int,
                                   organization_id: str,
                                   file_name: Optional[str] = "unknown_file.docx",
                                   use_match_ai_client_v2: bool = False) -> Dict[str, Any]:
       # This is the existing code for v2, just placed below.
       # It still uses the self._match_ai_client logic.
       # This method name is confusing. Let's rename it to process_uploaded_resume_v2.
       # The actual call from routes will explicitly say process_uploaded_resume_v1 or process_uploaded_resume_v2.
       pass # This method will be removed/renamed in routes
   
    def process_uploaded_resume_v3(self,
                                    file_path: str, # CRITICAL CHANGE: Accepts file path
                                    user_id: int,
                                    organization_id: str,
                                    file_name: Optional[str] = "unknown_file.docx",
                                    filebatchid: Optional[str] = None) -> Dict[str, Any]:
        """
        Processes an uploaded resume file using the V3 (MatchAIClient) parsing method.
        It expects the file to already be saved to disk at file_path.
        Includes DOCX/PDF extraction, calculations, embedding, and storage.
        """
        logger.info(f"Processing resume '{file_name}' from path '{file_path}' for user {user_id} in org {organization_id} (V3 method using MatchAIClient).")

        if self._match_ai_client is None:
            logger.error("MatchAIClient is not available for V3 processing.")
            raise RuntimeError("MatchAIClient service is not available. Check app.py initialization.")

        try:
            # MatchAIClient.extract_all directly accepts the file path
            llm_parsed_data = self._match_ai_client.extract_all(file_path, log_token_usage=True)
            logger.info(f"MatchAIClient parsing  {llm_parsed_data}")
            logger.info(f"MatchAIClient parsing successful for {llm_parsed_data.get('name', 'Unknown')}.")
            
            # Add file storage path to parsed data for later retrieval if needed
            llm_parsed_data['storage_path'] = file_path # Store the path as is
            
            # --- Apply additional calculations on MatchAI's output ---
            if 'organization_switches' not in llm_parsed_data:
                llm_parsed_data["organization_switches"] = self.data_analyzer_service.calculate_organization_switches(
                    llm_parsed_data.get("work_experiences", []) # Assuming MatchAI returns 'work_experiences' key
                )
            
            if 'time_spent_in_org' not in llm_parsed_data:
                if 'work_experiences' in llm_parsed_data:
                    llm_parsed_data['time_spent_in_org'] = self.data_analyzer_service.calculate_time_spent_in_organizations_v2(
                        llm_parsed_data.get('work_experiences', [])
                    )
                else:
                    llm_parsed_data['time_spent_in_org'] = self.data_analyzer_service.calculate_time_spent_in_organizations(
                        llm_parsed_data.get('experience', []) # Fallback to 'experience' if 'work_experiences' not present
                    )
            
            if 'total_experience_years' not in llm_parsed_data or llm_parsed_data['total_experience_years'] is None:
                if 'YoE' in llm_parsed_data and llm_parsed_data['YoE'] is not None:
                    llm_parsed_data['total_experience_years'] = llm_parsed_data['YoE']
                    logger.info(f"V3: Using MatchAIClient-provided YoE for total_experience_years: {llm_parsed_data['total_experience_years']}.")
                elif 'work_experiences' in llm_parsed_data:
                    llm_parsed_data['total_experience_years'] = self.data_analyzer_service.calculate_total_experience_v2(
                        llm_parsed_data.get('work_experiences', [])
                    )
                    logger.info(f"V3: Calculated total_experience_years using v2 method: {llm_parsed_data['total_experience_years']}.")
                else:
                    llm_parsed_data['total_experience_years'] = self.data_analyzer_service.calculate_total_experience(
                        llm_parsed_data.get('experience', [])
                    )
                    logger.info(f"V3: Calculated total_experience_years using v1 method (MatchAIClient did not provide explicit 'YoE' or 'work_experiences').")

            # llm_parsed_data['technology_experience_years'] = self.data_analyzer_service.calculate_technology_experience_years(
            #     llm_parsed_data
            # )

            text_for_embedding = self.embedding_service.build_text_for_embedding(llm_parsed_data)
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            
            # if embedding:
            #     llm_parsed_data['embedding'] = embedding
            # else:
            #     logger.warning(f"V3: Failed to generate embedding for profile: {llm_parsed_data.get('name', 'Unknown')}")
            #     llm_parsed_data['embedding'] = None 

            profile_id = self.profile_repository.save_profile(
                profile_data=llm_parsed_data,
                embedding=embedding,
                user_id=user_id,
                organization_id=organization_id,
                filebatchid=filebatchid
            )
            logger.info(f"V3: Profile for {llm_parsed_data.get('name', 'Unknown')} stored successfully with DB ID: {profile_id}")

            llm_parsed_data['db_id'] = profile_id

            return llm_parsed_data

        except ValueError as ve:
            logger.error(f"V3: Data validation error: {ve}", exc_info=True)
            raise 
        except Exception as e:
            logger.error(f"V3: An unexpected error occurred during resume processing: {e}", exc_info=True)
            raise 
        finally:
            # No file cleanup here, as it's handled by the calling route's finally block
            pass

    def get_profile_count_for_organization(self, organization_id: str, organization_type: str) -> int:
        """
        Gets the count of profiles for an organization,
        differentiating logic for OWN vs AGENCY organization types.
        """
        logger.info(f"Getting profile count for org: {organization_id} with type: {organization_type}")

        # If the user's organization is an 'AGENCY', we count profiles they manage via parent_org_id.
        # Otherwise, for 'OWN' or other types, we count profiles they own via organization_id.
        is_agency = organization_type and organization_type.lower() == 'agency'

        count = self.profile_repository.count_profiles_for_organization(
            organization_id=organization_id,
            by_parent_org=is_agency
        )
        
        return count
        
