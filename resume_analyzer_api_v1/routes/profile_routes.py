# routes/profile_routes.py
from flask import Blueprint, request, jsonify, Response, current_app, g # Ensure g is imported
import io
import json
import logging

from services.resume_parser_service import ResumeParserService
from services.data_analyzer_service import DataAnalyzerService
from services.embedding_service import EmbeddingService
from database.profile_repository import ProfileRepository
from auth.auth_routes import auth_required # Import the decorator
import jwt # <--- ENSURE THIS IMPORT IS PRESENT
import tempfile # <--- ADD THIS IMPORT
import os       # <--- ADD THIS IMPORT
#     from document_processor import DocumentProcessor
from services.document_processor import DocumentProcessor
from services.bulk_file_processor_service import BulkFileProcessorService 

# NEW: Import ProfileManagementService
from services.profile_management_service import ProfileManagementService

# NEW: Import MatchAIClient for initialization
from matchai import MatchAIClient # Ensure this path is correct for your MatchAIClient library
# If MatchAIClient lives in a subfolder like 'matchai/matchai.py', it would be:
# from matchai.matchai import MatchAIClient 
# Assuming 'matchai' is a top-level package next to 'services', 'routes' etc.
from plugin_registry import PLUGIN_REGISTRY # Assuming PLUGIN_REGISTRY is here

profile_bp = Blueprint('profile_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly


# WITH API VERSIONING
# USE THIS FOR FUTURE
# --- API Version 1 Endpoint ---
@profile_bp.route('/v1/upload_resume', methods=['POST']) # CHANGED ROUTE PATH
@auth_required # Protect this route
def upload_resume_v1(): # RENAMED FUNCTION
    """
    API endpoint (V1) to upload a .docx resume, processed by ProfileManagementService
    using the internal LLM parsing. Accepts an optional 'organization_id' query parameter.
    If not provided, it defaults to the user's own organization.
    """
    target_organization_id = request.args.get('organization_id')
    logger.info(f"target_organization_id {target_organization_id}")
    if not target_organization_id:
        target_organization_id = g.organization_id
        logger.info(f"Using authenticated user's organization ID: {target_organization_id} for resume upload (no query param).")
    else:
        logger.info(f"Using organization ID from query param: {target_organization_id} for resume upload (User's actual org: {g.organization_id}).")

    if not target_organization_id:
        logger.error("Organization ID is missing (neither in query param nor from authenticated user).")
        return jsonify({"error": "Target Organization ID is required for resume upload."}), 400

    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} uploading resume to target org {target_organization_id} via V1.")

    if 'resume' not in request.files:
        logger.error("V1: No resume file provided in the request.")
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        logger.error("V1: No selected file name in the request.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.docx'):
        logger.error(f"V1: Unsupported file format: {file.filename}. Only .docx is allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .docx file."}), 400

    try:
        profile_management_service: ProfileManagementService = current_app.profile_management_service

        # Determine the organization type to pass to the service.
        # If the target org is the user's own org, we can use the type from the session to save a DB call.
        # Otherwise, we pass None and let the service layer fetch it to ensure correctness.
        jd_organization_type_from_context = None
        if target_organization_id == g.organization_id:
            jd_organization_type_from_context = g.organization_type

        # Determine the correct parent_org_id for the Profile.
        # This logic mirrors the JD upload logic. If an agency user uploads a profile,
        # their organization is the parent.
        parent_org_id_for_profile = None
        if g.organization_type and g.organization_type.lower() == 'agency':
            # The logged-in user is from an agency. Their org ID is the parent.
            parent_org_id_for_profile = g.organization_id
            logger.info(f"Agency user {g.user_id} is uploading profile. Setting parent_org_id to agency's ID: {parent_org_id_for_profile}")
        else:
            # The logged-in user is from a client or other org type.
            # The parent_org_id comes from their session token (if they are managed by an agency).
            parent_org_id_for_profile = getattr(g, 'parent_org_id', None)
            if parent_org_id_for_profile:
                logger.info(f"Client user {g.user_id} is uploading profile. Using parent_org_id from session: {parent_org_id_for_profile}")

        # Call the service method for V1 processing
        llm_parsed_data = profile_management_service.process_uploaded_resume_v1(
            file_stream=io.BytesIO(file.read()),
            user_id=g.user_id,
            organization_id=target_organization_id,
            file_name=file.filename,
            jd_organization_type=jd_organization_type_from_context,
            parent_org_id=parent_org_id_for_profile
        )
        
        logger.info("V1: Resume processed and stored successfully. Returning prettified JSON.")
        
        pretty_json = json.dumps(llm_parsed_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"V1: Data validation error: {ve}", exc_info=True)
        return jsonify({"error": f"LLM parsing or data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"V1: An unexpected error occurred during resume processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# API Version 3 Endpoint (now calls process_uploaded_resume_v3)
# USE THIS FOR FUTURE
@profile_bp.route('/v3/upload_resume', methods=['POST'])
@auth_required
def upload_resume_v3():
    """
    API endpoint (V3) to upload a .docx (or .pdf) resume, processed by ProfileManagementService
    using the MatchAIClient.
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} uploading resume via V2 (MatchAIClient).")

    if 'resume' not in request.files:
        logger.error("V3: No resume file provided in the request.")
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        logger.error("V3: No selected file name in the request.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(('.docx', '.pdf')):
        logger.error(f"V3: Unsupported file format: {file.filename}. Only .docx or .pdf are allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .docx or .pdf file."}), 500

    temp_file_path = None # Initialize to None for finally block
    try:
        # CRITICAL CHANGE: Save the uploaded file to a temporary path here in the route.
        # MatchAIClient.extract_all needs a file path.
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"uploaded_resume_{os.urandom(8).hex()}_{file.filename}")
        
        file.save(temp_file_path) # Save the Werkzeug FileStorage object to disk
        logger.info(f"V3: Saved uploaded file to temporary path: {temp_file_path}")

        profile_management_service: ProfileManagementService = current_app.profile_management_service

        # Call the service method, passing the FILE PATH (not the stream)
        llm_parsed_data = profile_management_service.process_uploaded_resume_v3( # Call the V3 logic
            file_path=temp_file_path, # Pass the file path
            user_id=g.user_id,
            organization_id=g.organization_id,
            file_name=file.filename # Keep file_name for logging/storage details
        )
        
        logger.info("V2: Resume processed and stored successfully. Returning prettified JSON.")
        
        pretty_json = json.dumps(llm_parsed_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"V2: Data validation error: {ve}", exc_info=True)
        return jsonify({"error": f"Data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"V2: An unexpected error occurred during resume processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    finally:
        # Ensure the temporary file is deleted from disk in the route's finally block
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"V2: Removed temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"V2: Error removing temporary file {temp_file_path}: {e}", exc_info=True)

# API VERSIONING CHANGE STOP


# DEPRECATE BELOW
@profile_bp.route('/upload-resume-b', methods=['POST'])
@auth_required # Protect this route
def upload_resume_b():
    """
    API endpoint (V1) to upload a .docx resume, processed by ProfileManagementService.
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} uploading resume via V1.")

    if 'resume' not in request.files:
        logger.error("No resume file provided in the request.")
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        logger.error("No selected file name in the request.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.docx'):
        logger.error(f"Unsupported file format: {file.filename}. Only .docx is allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .docx file."}), 400

    try:
        profile_management_service: ProfileManagementService = current_app.profile_management_service

        # Call the new service method to handle all the logic for V1
        llm_parsed_data = profile_management_service.process_uploaded_resume_v1(
            file_stream=io.BytesIO(file.read()), # Pass the BytesIO stream
            user_id=g.user_id,
            organization_id=g.organization_id,
            file_name=file.filename # Pass file_name for logging/temp
        )
        
        logger.info("Resume processed and stored successfully. Returning prettified JSON.")
        
        pretty_json = json.dumps(llm_parsed_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"LLM parsing or data validation error: {ve}", exc_info=True)
        return jsonify({"error": f"LLM parsing or data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during resume processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# DEPRECATE BELOW
@profile_bp.route('/upload-resume', methods=['POST'])
@auth_required # Protect this route
def upload_resume():
    """
    API endpoint to upload a .docx resume, parse it using Gemini LLM,
    perform calculations, generate embedding, and store in PostgreSQL
    associated with the authenticated user and organization.
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} uploading resume.")

    if 'resume' not in request.files:
        logger.error("No resume file provided in the request.")
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        logger.error("No selected file name in the request.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith('.docx'):
        logger.error(f"Unsupported file format: {file.filename}. Only .docx is allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .docx file."}), 400

    try:
        resume_parser_service: ResumeParserService = current_app.resume_parser_service
        data_analyzer_service: DataAnalyzerService = current_app.data_analyzer_service
        embedding_service: EmbeddingService = current_app.embedding_service
        profile_repository: ProfileRepository = current_app.profile_repository

        docx_content_stream = io.BytesIO(file.read())
        

        # CHANGES FOR COMBINED
        # raw_resume_text = resume_parser_service.extract_text_from_docx(docx_content_stream)
        
        document_processor = DocumentProcessor(docx_content_stream)
        raw_resume_text = document_processor.get_combined_document_content()

        # raw_resume_text = document_processor.extract_text_from_docxv2(docx_content_stream)
        # END

        logger.debug(f"Raw String is {raw_resume_text}")
        llm_parsed_data = resume_parser_service.parse_resume_with_gemini(raw_resume_text) 
        
        llm_parsed_data["organization_switches"] = data_analyzer_service.calculate_organization_switches(
            llm_parsed_data.get("experience", [])
        )
        llm_parsed_data['technology_experience_years'] = data_analyzer_service.calculate_technology_experience_years(
            llm_parsed_data
        )
        llm_parsed_data['time_spent_in_org'] = data_analyzer_service.calculate_time_spent_in_organizations(
            llm_parsed_data.get('experience', [])
        )
        
        if 'total_experience_years' not in llm_parsed_data or llm_parsed_data['total_experience_years'] is None:
            llm_parsed_data['total_experience_years'] = data_analyzer_service.calculate_total_experience(
                llm_parsed_data.get('experience', [])
            )
            logger.info(f"Calculated total_experience_years as {llm_parsed_data['total_experience_years']} (LLM did not provide explicitly).")
        else:
            logger.info(f"Using LLM-provided total_experience_years: {llm_parsed_data['total_experience_years']}.")

        text_for_embedding = embedding_service.build_text_for_embedding(llm_parsed_data)
        embedding = embedding_service.generate_embedding(text_for_embedding)
        
        # Get user_id and organization_id from the authenticated context (g)
        user_id_for_db = g.user_id
        organization_id_for_db = g.organization_id

        if not user_id_for_db or not organization_id_for_db:
            logger.error("User ID or Organization ID missing from authenticated context.")
            return jsonify({"error": "Authentication context incomplete for saving profile."}), 500

        # Store in PostgreSQL, passing user_id and organization_id explicitly
        profile_id = profile_repository.save_profile(
            profile_data=llm_parsed_data, # This is the JSONB blob
            embedding=embedding,
            user_id=user_id_for_db,
            organization_id=organization_id_for_db
        )
        logger.info(f"Profile for {llm_parsed_data.get('name', 'Unknown')} stored successfully with DB ID: {profile_id}")

        # Add the DB ID to the response for confirmation
        llm_parsed_data['db_id'] = profile_id

        logger.info("Resume processed and stored successfully. Returning prettified JSON.")
        
        pretty_json = json.dumps(llm_parsed_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"LLM parsing or data validation error: {ve}")
        return jsonify({"error": f"LLM parsing or data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during resume processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# DEPRECATE BELOW
# NEW: Version 2 Upload Endpoint using MatchAIClient
@profile_bp.route('/v2/upload_resume', methods=['POST'])
@auth_required
def upload_resume_v2():
    """
    API endpoint (V2) to upload a .docx (or .pdf) resume, process it via MatchAIClient,
    perform additional calculations, generate embedding, and store in PostgreSQL
    associated with the authenticated user and organization.
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} uploading resume via V2 (MatchAIClient).")

    # Check if MatchAIClient is initialized (it might be None if import failed in app.py)
    if current_app.match_ai_client is None:
        logger.error("MatchAIClient is not initialized. Cannot process V2 upload.")
        return jsonify({"error": "MatchAI service is not available. Check server logs."}), 503 # Service Unavailable

    if 'resume' not in request.files:
        logger.error("V2: No resume file provided in the request.")
        return jsonify({"error": "No resume file provided"}), 400

    file = request.files['resume']
    if file.filename == '':
        logger.error("V2: No selected file name in the request.")
        return jsonify({"error": "No selected file"}), 400

    # MatchAIClient might handle PDF too based on sample usage; check both .docx and .pdf
    if not file.filename.lower().endswith(('.docx', '.pdf')):
        logger.error(f"V2: Unsupported file format: {file.filename}. Only .docx or .pdf are allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .docx or .pdf file."}), 400

    temp_file_path = None # Initialize to None
    try:
        # Save the uploaded file to a temporary location for MatchAIClient
        # tempfile.NamedTemporaryFile creates a unique temporary file and handles deletion.
        # However, for `file.save()`, we need a path that persists until MatchAIClient reads it.
        # Using a temporary directory and joining path is a robust way.
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"uploaded_resume_{os.urandom(8).hex()}_{file.filename}")
        
        file.save(temp_file_path) # Save the uploaded file to the temporary path
        logger.info(f"V2: Saved uploaded file to temporary path: {temp_file_path}")

        # Access MatchAIClient from app context
        match_ai_client = current_app.match_ai_client # Type hint not strictly needed here but good practice
        data_analyzer_service: DataAnalyzerService = current_app.data_analyzer_service
        embedding_service: EmbeddingService = current_app.embedding_service
        profile_repository: ProfileRepository = current_app.profile_repository

        # Call MatchAIClient to extract all information
        # Pass log_token_usage as True as per sample
        llm_parsed_data = match_ai_client.extract_all(temp_file_path, log_token_usage=True)
        logger.info(f"V2: MatchAIClient parsing successful for {llm_parsed_data.get('name', 'Unknown')}.")

        # Apply additional calculations on MatchAI's output
        # These calculations ensure consistency with our defined JSON structure and metrics.

        # 1. Calculate Organization Switches
        if 'organization_switches' not in llm_parsed_data: # If MatchAIClient doesn't provide it
            llm_parsed_data["organization_switches"] = data_analyzer_service.calculate_organization_switches(
                llm_parsed_data.get("work_experiences", [])
            )
        
        # 2. Calculate Time Spent in Each Organization
        if 'time_spent_in_org' not in llm_parsed_data: # If MatchAIClient doesn't provide it
            llm_parsed_data['time_spent_in_org'] = data_analyzer_service.calculate_time_spent_in_organizations_v2(
                llm_parsed_data.get('work_experiences', [])
            )
        
        # 3. Calculate Total Experience Years
        # Prioritize MatchAIClient's extracted value. If missing, calculate using our service.
        logger.debug(f"Totl expereince in years {llm_parsed_data['YoE']}")
        llm_parsed_data['total_experience_years'] = llm_parsed_data['YoE']
        if 'total_experience_years' not in llm_parsed_data or llm_parsed_data['total_experience_years'] is None:
            
            llm_parsed_data['total_experience_years'] = data_analyzer_service.calculate_total_experience(
                llm_parsed_data.get('work_experiences', [])
            )
            logger.info(f"V2: Calculated total_experience_years as {llm_parsed_data['total_experience_years']} (MatchAIClient did not provide explicitly).")
        else:
            logger.info(f"V2: Using MatchAIClient-provided total_experience_years: {llm_parsed_data['total_experience_years']}.")

        # 4. Calculate Technology Experience Years (Our custom calculation, often not done by basic parsers)
        # This will always be recalculated by our service for consistency.


        # 5. Generate Embedding for Semantic Search (Always use our EmbeddingService)
        text_for_embedding = embedding_service.build_text_for_embedding(llm_parsed_data)
        embedding = embedding_service.generate_embedding(text_for_embedding)
        
        # Store embedding in the parsed data (JSONB) if you want it there,
        # in addition to the dedicated vector column in PostgreSQL.
        # if embedding:
        #     llm_parsed_data['embedding'] = embedding
        # else:
        #     logger.warning(f"V2: Failed to generate embedding for profile: {llm_parsed_data.get('name', 'Unknown')}")
        #     llm_parsed_data['embedding'] = None 

        llm_parsed_data['embedding'] = None 
        # Get user_id and organization_id from the authenticated context (g)
        user_id_for_db = g.user_id
        organization_id_for_db = g.organization_id

        if not user_id_for_db or not organization_id_for_db:
            logger.error("V2: User ID or Organization ID missing from authenticated context.")
            return jsonify({"error": "Authentication context incomplete for saving profile."}), 500

        # Store in PostgreSQL
        profile_id = profile_repository.save_profile(
            profile_data=llm_parsed_data, # This is the JSONB blob
            embedding=embedding,
            user_id=user_id_for_db,
            organization_id=organization_id_for_db
        )
        logger.info(f"V2: Profile for {llm_parsed_data.get('name', 'Unknown')} stored successfully with DB ID: {profile_id}")

        llm_parsed_data['db_id'] = profile_id # Add DB ID to the response

        logger.info("V2: Resume processed and stored successfully. Returning prettified JSON.")
        
        pretty_json = json.dumps(llm_parsed_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"V2: Data validation error: {ve}", exc_info=True)
        return jsonify({"error": f"Data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"V2: An unexpected error occurred during resume processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    finally:
        # Ensure the temporary file is deleted
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"V2: Removed temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"V2: Error removing temporary file {temp_file_path}: {e}", exc_info=True)


# Semantic Search and Filter Profiles routes (should also use @auth_required and filter by g.organization_id)
@profile_bp.route('/semantic-search', methods=['GET'])
@auth_required
def semantic_search_profiles():
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} performing semantic search.")
    query_text = request.args.get('query', '')
    if not query_text:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    logger.info(f"Received semantic search request for query: '{query_text}'")
    try:
        embedding_service: EmbeddingService = current_app.embedding_service
        profile_repository: ProfileRepository = current_app.profile_repository

        query_embedding = embedding_service.generate_embedding(query_text)
        if not query_embedding:
            return jsonify({"error": "Failed to generate embedding for query"}), 500

        # Pass organization_id to filter results
        search_results = profile_repository.semantic_search_profiles(
            query_embedding, 
            organization_id=g.organization_id
        )
        
        filtered_results = [{"name": r["name"], "score": round(r["similarity_score"], 4)} for r in search_results]
        
        logger.info(f"Found {len(filtered_results)} profiles for semantic query '{query_text}' in org '{g.organization_id}'")
        return jsonify({"profiles": filtered_results}), 200
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred during semantic search: {str(e)}"}), 500

@profile_bp.route('/filter-profiles', methods=['GET'])
@auth_required
def filter_profiles():
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} performing filtered search.")
    filters = {}
    if 'name' in request.args:
        filters['name'] = request.args['name']
    if 'min_total_yoe' in request.args:
        try:
            filters['min_total_yoe'] = float(request.args['min_total_yoe'])
        except ValueError:
            return jsonify({"error": "min_total_yoe must be a number"}), 400
    if 'qualification' in request.args:
        filters['qualification'] = request.args['qualification']
    if 'skill' in request.args:
        filters['skill'] = request.args['skill']
    if 'tech_experience.name' in request.args and 'tech_experience.min_years' in request.args:
        try:
            filters['tech_experience'] = {
                'name': request.args['tech_experience.name'],
                'min_years': float(request.args['tech_experience.min_years'])
            }
        except ValueError:
            return jsonify({"error": "tech_experience.min_years must be a number"}), 400

    if not filters:
        return jsonify({"error": "No filter criteria provided"}), 400

    logger.info(f"Received filter request with criteria: {filters} for org '{g.organization_id}'")
    try:
        profile_repository: ProfileRepository = current_app.profile_repository
        # Pass organization_id to filter results
        filtered_profiles = profile_repository.filter_profiles_by_criteria(
            filters, 
            organization_id=g.organization_id
        )
        return jsonify({"profiles": filtered_profiles}), 200
    except Exception as e:
        logger.error(f"Error during profile filtering: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred during filtering: {str(e)}"}), 500
    
    
# --- NEW ENDPOINT: Bulk Resume Upload (ZIP File) ---
@profile_bp.route('/v1/bulk_upload_resume', methods=['POST']) 
@auth_required
def bulk_upload_resume():
    """
    API endpoint (V1) to upload a ZIP file containing multiple resumes for bulk processing.
    Expects organization_id and job_id as query parameters.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} initiating bulk resume upload.")

    organization_id = request.args.get('organization_id')
    job_id_str = request.args.get('job_id')

    if not organization_id:
        return jsonify({"error": "organization_id query parameter is required"}), 400
    if not job_id_str:
        return jsonify({"error": "job_id query parameter is required"}), 400

    try:
        job_id = int(job_id_str)
    except ValueError:
        return jsonify({"error": "job_id must be an integer"}), 400

    if 'zip_file' not in request.files:
        logger.error("No ZIP file provided in the request.")
        return jsonify({"error": "No ZIP file provided"}), 400

    zip_file = request.files['zip_file']
    if zip_file.filename == '':
        logger.error("No selected ZIP file name in the request.")
        return jsonify({"error": "No selected ZIP file"}), 400

    if not zip_file.filename.lower().endswith('.zip'):
        logger.error(f"Unsupported file format: {zip_file.filename}. Only .zip is allowed.")
        return jsonify({"error": "Unsupported file format. Please upload a .zip file."}), 400

    try:
        # CRITICAL FIX: Call BulkFileProcessorService directly
        bulk_processor_service: BulkFileProcessorService = current_app.bulk_file_processor_service

        # Pass the BytesIO stream of the zip file, org_id, job_id, and file_name to the service
        # Also pass g.user_id for 'created_by' in individual resume processing
        processing_summary = bulk_processor_service.process_zip_file_for_resumes_v2(
            zip_file_stream=io.BytesIO(zip_file.read()),
            user_id=g.user_id, # Pass the authenticated user_id
            organization_id=organization_id,
            job_id=job_id,
            file_name=zip_file.filename,
            # use_match_ai_client_v2 can be added as a query param if needed
            use_match_ai_client_v2=request.args.get('use_match_ai_client_v2', 'false').lower() == 'true'
        )
        
        return jsonify(processing_summary), 200

    except ValueError as ve:
        logger.error(f"Bulk upload validation error: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred during bulk upload: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# --- NEW ENDPOINT: Get Bulk Upload History ---
@profile_bp.route('/v1/bulk_upload_list', methods=['GET'])
@auth_required
def get_bulk_upload_list():
    """
    API endpoint to retrieve the history of bulk uploads for a specific job.
    Filters by organization_id, job_id, and the authenticated user.
    Optionally filters by a date range (start_date, end_date).
    """
    logger.info(f"User {g.user_id} from org {g.organization_id} requesting bulk upload list.")

    # --- Get required query parameters ---
    organization_id = request.args.get('organization_id')
    job_id_str = request.args.get('job_id')

    if not organization_id:
        return jsonify({"error": "organization_id query parameter is required"}), 400
    if not job_id_str:
        return jsonify({"error": "job_id query parameter is required"}), 400

    # --- Validate job_id ---
    try:
        job_id = int(job_id_str)
    except ValueError:
        return jsonify({"error": "job_id must be an integer"}), 400

    # --- Get optional query parameters ---
    start_date = request.args.get('start_date') # e.g., 'YYYY-MM-DD'
    end_date = request.args.get('end_date')     # e.g., 'YYYY-MM-DD'

    # --- Get user_id from authenticated context ---
    user_id = g.user_id

    logger.info(f"Fetching bulk upload list for org: {organization_id}, job: {job_id}, user: {user_id}, start: {start_date}, end: {end_date}")

    try:
        bulk_processor_service: BulkFileProcessorService = current_app.bulk_file_processor_service

        upload_history = bulk_processor_service.get_bulk_upload_history(
            organization_id=organization_id, job_id=job_id, user_id=user_id, start_date=start_date, end_date=end_date
        )
        
        return jsonify({"upload_history": upload_history}), 200

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching bulk upload list: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


@profile_bp.route('/v1/profile_count', methods=['GET'])
@auth_required
def get_profile_count():
    """
    API endpoint to get the count of profiles for the user's organization.
    The logic adapts based on whether the user's organization is of type 'OWN' or 'AGENCY'.
    If 'AGENCY', it counts profiles where parent_org_id matches the user's org.
    Otherwise, it counts profiles where organization_id matches.
    """
    user_org_id = g.organization_id
    user_org_type = g.organization_type

    logger.info(f"User {g.user_id} from org {user_org_id} (type: {user_org_type}) requesting profile count.")

    if not user_org_id or not user_org_type:
        return jsonify({"error": "User organization context is incomplete."}), 400

    try:
        profile_management_service: ProfileManagementService = current_app.profile_management_service
        
        count = profile_management_service.get_profile_count_for_organization(
            organization_id=user_org_id,
            organization_type=user_org_type
        )
        
        return jsonify({"organizationId": user_org_id, "profileCount": count}), 200

    except Exception as e:
        logger.error(f"Error getting profile count for org {user_org_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500
