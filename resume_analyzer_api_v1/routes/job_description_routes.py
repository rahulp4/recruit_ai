# routes/job_description_routes.py

from flask import Blueprint, request, jsonify, Response, current_app, g
import io
import json
import logging

from services.job_description_management_service import JobDescriptionManagementService # Import JD Management Service
from auth.auth_routes import auth_required # Import the decorator

jd_bp = Blueprint('jd_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

@jd_bp.route('/v1/upload_jd', methods=['POST'])
@auth_required 
def upload_job_description():
    """
    API endpoint (V1) to upload a Job Description (JD) file (DOCX/PDF) and parse it.
    Expects organization_id as an optional query parameter for multi-tenancy.
    Also accepts 'user_tags' (comma-separated) and 'is_active' (boolean) as optional query parameters.
    """
    target_organization_id = request.args.get('organization_id')
    if not target_organization_id:
        target_organization_id = g.organization_id
        logger.info(f"Using authenticated user's organization ID: {target_organization_id} for JD upload (no query param).")
    else:
        logger.info(f"Using organization ID from query param: {target_organization_id} for JD upload (User's actual org: {g.organization_id}).")

    if not target_organization_id:
        logger.error("Organization ID is missing (neither in query param nor from authenticated user).")
        return jsonify({"error": "Target Organization ID is required for JD upload."}), 400

    # NEW: Get user_tags from query parameter
    user_tags_str = request.args.get('user_tags')
    user_tags_list = [tag.strip() for tag in user_tags_str.split(',')] if user_tags_str else []
    if user_tags_list:
        logger.info(f"Received user tags: {user_tags_list}")

    # NEW: Get is_active from query parameter
    is_active_str = request.args.get('is_active')
    is_active_bool = True # Default to True
    if is_active_str is not None:
        is_active_bool = is_active_str.lower() == 'true'
    logger.info(f"JD is_active status: {is_active_bool}")

    # NEW: Get jd_version from query parameter
    jd_version_str = request.args.get('jd_version')
    jd_version_int = 1 # Default to version 1
    if jd_version_str is not None:
        try:
            jd_version_int = int(jd_version_str)
        except ValueError:
            return jsonify({"error": "jd_version must be an integer"}), 400
    logger.info(f"JD version: {jd_version_int}")

    # NEW: Determine the organization type to pass to the service.
    # If the target org is the user's own org, we can use the type from the session to save a DB call.
    # Otherwise, we pass None and let the service layer fetch it to ensure correctness.
    jd_organization_type_from_context = None
    if target_organization_id == g.organization_id:
        jd_organization_type_from_context = g.organization_type

    # --- Determine the correct parent_org_id for the Job Description ---
    # The parent_org_id for a JD is the ID of the agency that manages it.
    # Case 1: An agency user is logged in. Their own org ID is the parent_org_id for any JD they upload (for themselves or a client).
    # Case 2: A client user is logged in. Their parent_org_id comes from their session token (if they are managed by an agency).
    parent_org_id_for_jd = None
    if g.organization_type and g.organization_type.lower() == 'agency':
        # The logged-in user is from an agency. Their org ID is the parent.
        parent_org_id_for_jd = g.organization_id
        logger.info(f"Agency user {g.user_id} is uploading JD. Setting parent_org_id to agency's ID: {parent_org_id_for_jd}")
    else:
        # The logged-in user is from a client or other org type.
        # The parent_org_id comes from their session token (if they are managed by an agency).
        parent_org_id_for_jd = getattr(g, 'parent_org_id', None)
        if parent_org_id_for_jd:
            logger.info(f"Client user {g.user_id} is uploading JD. Using parent_org_id from session: {parent_org_id_for_jd}")


    if 'jd_file' not in request.files:
        logger.error("No JD file provided in the request.")
        return jsonify({"error": "No JD file provided"}), 400

    jd_file = request.files['jd_file']
    if jd_file.filename == '':
        logger.error("No selected JD file name in the request.")
        return jsonify({"error": "No selected JD file"}), 400

    if not jd_file.filename.lower().endswith(('.docx', '.pdf')):
        logger.error(f"Unsupported JD file format: {jd_file.filename}. Only .docx or .pdf are allowed.")
        return jsonify({"error": "Unsupported JD file format. Please upload a .docx or .pdf file."}), 500

    try:
        jd_management_service: JobDescriptionManagementService = current_app.jd_management_service

        parsed_jd_data = jd_management_service.process_uploaded_jd(
            jd_file_stream=io.BytesIO(jd_file.read()),
            user_id=g.user_id, 
            organization_id=target_organization_id, 
            file_name=jd_file.filename,
            current_user_org_id=g.organization_id,
            current_user_roles=g.user_roles,
            user_tags=user_tags_list, # Pass user_tags
            is_active=is_active_bool, # Pass is_active
            jd_version=jd_version_int, # Pass jd_version
            jd_organization_type=jd_organization_type_from_context, # NEW: Pass the type from context
            parent_org_id=parent_org_id_for_jd # NEW: Pass the correctly determined parent org id
        )
        
        logger.info(f"Job Description processed successfully for title: {parsed_jd_data.get('job_title', 'Unknown')} in org {target_organization_id}.")
        
        pretty_json = json.dumps(parsed_jd_data, indent=2)
        return Response(pretty_json, mimetype='application/json'), 200

    except ValueError as ve:
        logger.error(f"JD parsing or data validation error: {ve}", exc_info=True)
        return jsonify({"error": f"JD parsing or data validation error: {str(ve)}"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during JD processing: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred during JD processing: {str(e)}"}), 500

@jd_bp.route('/v1/semantic_search_jd', methods=['GET'])
@auth_required # Protect this endpoint
def semantic_search_job_descriptions():
    """
    API endpoint to perform semantic search on stored Job Descriptions.
    Filters by the authenticated user's organization.
    Accepts 'is_active' (boolean), 'user_tag' (string), and 'min_similarity' (float) as optional query parameters.
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} requesting semantic search on JDs.")

    query_text = request.args.get('query', '')
    if not query_text:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    # NEW: Get min_similarity filter
    min_similarity_str = request.args.get('min_similarity')
    min_similarity_float = 0.1 # Default minimum similarity
    if min_similarity_str:
        try:
            min_similarity_float = float(min_similarity_str)
        except ValueError:
            return jsonify({"error": "min_similarity must be a number"}), 400

    # NEW: Get is_active and user_tag filters
    filters = {}
    is_active_str = request.args.get('is_active')
    if is_active_str is not None:
        filters['is_active'] = is_active_str.lower() == 'true'
    
    user_tag = request.args.get('user_tag')
    if user_tag:
        filters['user_tag'] = user_tag

    # NEW: Get jd_version filter for semantic search
    jd_version_str = request.args.get('jd_version')
    if jd_version_str is not None:
        try:
            filters['jd_version'] = int(jd_version_str)
        except ValueError:
            return jsonify({"error": "jd_version must be an integer"}), 400
    

    logger.info(f"Received semantic search request for JDs: '{query_text}' with filters: {filters} and min_similarity: {min_similarity_float}.")

    try:
        embedding_service = current_app.embedding_service
        jd_repository: JobDescriptionRepository = current_app.jd_repository

        query_embedding = embedding_service.generate_embedding(query_text)
        if not query_embedding:
            return jsonify({"error": "Failed to generate embedding for search query"}), 500

        search_results = jd_repository.semantic_search_job_descriptions(
            query_embedding=query_embedding,
            organization_id=g.organization_id, 
            limit=10, # Keep limit or make it configurable
            min_similarity=min_similarity_float, # Pass to repository
            filters=filters 
        )
        
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "id": result.get('id'),
                "jobTitle": result.get('job_title'), 
                "location": result.get('location'),
                "organizationId": result.get('orgid'), 
                "userId": result.get('userid'),       
                "userTags": result.get('userTags'), 
                "isActive": result.get('isActive'), 
                "jdVersion": result.get('jdVersion'), # Include jdVersion
                "similarityScore": result.get('similarityScore')
            })
        
        logger.info(f"Found {len(formatted_results)} JDs for semantic query '{query_text}' in org '{g.organization_id}'.")
        return jsonify({"jobDescriptions": formatted_results}), 200

    except Exception as e:
        logger.error(f"Error during semantic search on JDs: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred during JD semantic search: {str(e)}"}), 500
        
# NEW ENDPOINT: Get list of JDs for an organization
@jd_bp.route('/v1/list_by_organization/<string:organization_id>', methods=['GET'])
@auth_required # Protect this endpoint
def get_jds_by_organization(organization_id: str):
    """
    API endpoint to get a list of Job Descriptions for a specified organization.
    Accepts 'include_inactive' (boolean), 'user_tag' (string), and 'jd_version' (int) as optional query parameters.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} requesting JD list for org {organization_id}.")
    logger.info(f"organization_type {g.organization_type}.")
    
    # Get filters for list
    include_inactive_str = request.args.get('include_inactive')
    include_inactive_bool = False 
    if include_inactive_str is not None:
        include_inactive_bool = include_inactive_str.lower() == 'true'
    
    user_tag = request.args.get('user_tag')
    
    jd_version_str = request.args.get('jd_version')
    jd_version_int = None # Default to None to not filter by version
    if jd_version_str is not None:
        try:
            jd_version_int = int(jd_version_str)
        except ValueError:
            return jsonify({"error": "jd_version must be an integer"}), 400
    
    try:
        jd_management_service: JobDescriptionManagementService = current_app.jd_management_service
        
        jds_list = jd_management_service.get_job_descriptions_for_organization(
            organization_id=organization_id,
            current_user_id=g.user_id,
            current_user_roles=g.user_roles,
            include_inactive=include_inactive_bool,
            user_tag=user_tag,
            jd_version=jd_version_int # Pass jd_version
        )
        
        return jsonify({"jobDescriptions": jds_list}), 200

    except PermissionError as pe:
        logger.error(f"Permission denied to list JDs for org {organization_id}: {pe}", exc_info=True)
        return jsonify({"error": str(pe)}), 403 
    except Exception as e:
        logger.error(f"Error listing JDs for organization {organization_id}: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred while listing JDs: {str(e)}"}), 500

@jd_bp.route('/v1/rule/<int:jd_id>', methods=['GET']) # NEW ENDPOINT: Get JD by ID
@auth_required 
def get_job_description_details(jd_id: int):
    """
    API endpoint to get a single Job Description's details by its ID.
    The user must have permission to view JDs for the associated organization.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} requesting JD details for ID: {jd_id}.")

    try:
        jd_management_service: JobDescriptionManagementService = current_app.jd_management_service
        
        jd_details = jd_management_service.get_job_description_details(
            jd_id=jd_id,
            organization_id=g.organization_id, # Filter by user's organization
            current_user_id=g.user_id,
            current_user_roles=g.user_roles
        )
        
        if jd_details:
            return jsonify(jd_details), 200
        return jsonify({"message": "Job Description not found or unauthorized access."}), 404

    except PermissionError as pe:
        logger.error(f"Permission denied to view JD {jd_id}: {pe}", exc_info=True)
        return jsonify({"error": str(pe)}), 403 
    except Exception as e:
        logger.error(f"Error retrieving JD {jd_id} details: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred while retrieving JD: {str(e)}"}), 500    

@jd_bp.route('/v1/active_count', methods=['GET'])
@auth_required
def get_active_jd_count():
    """
    API endpoint to get the count of active job descriptions for the user's organization.
    The logic adapts based on whether the user's organization is of type 'OWN' or 'AGENCY'.
    """
    user_org_id = g.organization_id
    user_org_type = g.organization_type

    logger.info(f"User {g.user_id} from org {user_org_id} (type: {user_org_type}) requesting active JD count.")

    if not user_org_id or not user_org_type:
        return jsonify({"error": "User organization context is incomplete."}), 400

    try:
        jd_management_service: JobDescriptionManagementService = current_app.jd_management_service
        
        count = jd_management_service.get_active_jd_count_for_organization(
            organization_id=user_org_id,
            organization_type=user_org_type
        )
        
        return jsonify({"organizationId": user_org_id, "activeJobDescriptionCount": count}), 200

    except Exception as e:
        logger.error(f"Error getting active JD count for org {user_org_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500