# routes/matching_routes.py

from flask import Blueprint, request, jsonify, Response, current_app, g
import logging
import json # For formatting response

from auth.auth_routes import auth_required # Import the decorator
from services.matching_engine_service import MatchingEngineService # Import the new service

match_bp = Blueprint('match_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

@match_bp.route('/v1/match', methods=['POST'])
@auth_required # Protect this endpoint
def initiate_match():
    """
    API endpoint (V1) to initiate a match between a Job Description and a Candidate Profile.
    Expects jobId and profileId in the JSON request body.
    Requires 'match:initiate' permission.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} initiating match.")
    
    data = request.get_json()
    job_id = data.get('jobId')
    profile_id = data.get('profileId')

    if job_id is None or profile_id is None:
        return jsonify({"error": "jobId and profileId are required in the request body"}), 400

    try:
        matching_engine_service: MatchingEngineService = current_app.matching_engine_service
        
        match_result = matching_engine_service.perform_match(
            job_id=job_id,
            profile_id=profile_id,
            current_user_id=g.user_id,
            current_org_id=g.organization_id,
            current_user_roles=g.user_roles # Pass roles for permission check
        )
        
        return jsonify(match_result), 200

    except PermissionError as pe:
        logger.error(f"Permission denied for match initiation: {pe}", exc_info=True)
        return jsonify({"error": str(pe)}), 403 # Forbidden
    except ValueError as ve:
        logger.error(f"Match initiation data validation error: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400 # Bad Request
    except Exception as e:
        logger.error(f"An unexpected error occurred during match initiation: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    
    
# NEW ENDPOINT: Search match results
@match_bp.route('/v1/search', methods=['GET'])
@auth_required # Protect this endpoint
def search_match_results():
    """
    API endpoint (V1) to search for previously saved job-profile match results.
    Filters by organization_id (from query param or authenticated user's org).
    Optional filters: job_id (int), candidate_name (string, partial).
    """
    target_organization_id = request.args.get('organization_id')
    if not target_organization_id:
        target_organization_id = g.organization_id
        logger.info(f"Using authenticated user's organization ID: {target_organization_id} for match search (no query param).")
    else:
        logger.info(f"Using organization ID from query param: {target_organization_id} for match search (User's actual org: {g.organization_id}).")
    
    if not target_organization_id:
        logger.error("Organization ID is missing (neither in query param nor from authenticated user).")
        return jsonify({"error": "Target Organization ID is required for match search."}), 400

    job_id_str = request.args.get('job_id')
    job_id = None
    if job_id_str:
        try:
            job_id = int(job_id_str)
        except ValueError:
            return jsonify({"error": "job_id must be an integer"}), 400

    candidate_name = request.args.get('candidate_name')
    
    limit_str = request.args.get('limit')
    limit = 100 # Default limit
    if limit_str:
        try:
            limit = int(limit_str)
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400

    order_by_score_desc_str = request.args.get('order_by_score_desc')
    order_by_score_desc = True # Default to descending
    if order_by_score_desc_str is not None:
        order_by_score_desc = order_by_score_desc_str.lower() == 'true'

    logger.info(f"User {g.user_id} (Org: {g.organization_id}) searching matches for target org {target_organization_id} with filters: job_id={job_id}, candidate_name='{candidate_name}', limit={limit}, order_by_score_desc={order_by_score_desc}.")

    try:
        matching_engine_service: MatchingEngineService = current_app.matching_engine_service
        
        search_results = matching_engine_service.search_match_results(
            organization_id=target_organization_id,
            current_user_id=g.user_id,
            current_user_roles=g.user_roles,
            job_id=job_id,
            candidate_name=candidate_name,
            limit=limit,
            order_by_score_desc=order_by_score_desc
        )
        
        return jsonify({"matchResults": search_results}), 200

    except PermissionError as pe:
        logger.error(f"Permission denied for match search: {pe}", exc_info=True)
        return jsonify({"error": str(pe)}), 403 
    except ValueError as ve:
        logger.error(f"Match search data validation error: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400 
    except Exception as e:
        logger.error(f"An unexpected error occurred during match search: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500    