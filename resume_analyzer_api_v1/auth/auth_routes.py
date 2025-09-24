# auth/auth_routes.py

from flask import Blueprint, request, jsonify, Response, current_app, g
import logging
import jwt 
from datetime import datetime, timedelta
from functools import wraps 

from auth.auth_service import AuthService
from services.resource_service import ResourceService 

auth_bp = Blueprint('auth_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

# --- Authentication Decorator for Protected Routes ---
def auth_required(f):
    """Decorator to protect API routes."""
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        if not session_token:
            logger.warning("Access denied:-- No session token provided.")
            response = jsonify({"message": "Authentication required"})
            response.set_cookie('is_logged_in_indicator', '', expires=0)
            return response, 401

        try:
            auth_service: AuthService = current_app.auth_service
            payload = auth_service.get_user_from_session_token(session_token)
            
            g.user_payload = payload 
            g.organization_id = payload.get('organizationId')
            g.organization_type = payload.get('organizationType') # NEW: Get org type from token
            g.parent_org_id = payload.get('parentOrgId') # NEW: Get parent org id from token
            g.firebase_uid = payload.get('uid')
            g.user_id = payload.get('userId') 
            g.user_roles = payload.get('roles', []) 

            
            if not g.organization_id or not g.user_id:
                 logger.error(f"CRITICAL: Organization ID or User DB ID missing after auth for Firebase UID {g.firebase_uid}.")
                 response = jsonify({"message": "Authentication context incomplete."})
                 response.set_cookie('session_token', '', expires=0) 
                 response.set_cookie('is_logged_in_indicator', '', expires=0)
                 return response, 401

            logger.debug(f"Authenticated request for UID: {g.firebase_uid}, DB User ID: {g.user_id} in Org: {g.organization_id}, Roles: {g.user_roles}")
            return f(*args, **kwargs)
        except ValueError as e: 
            logger.warning(f"Access denied: {e}")
            response = jsonify({"message": str(e)})
            response.set_cookie('session_token', '', expires=0) 
            response.set_cookie('is_logged_in_indicator', '', expires=0)
            return response, 401
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            response = jsonify({"message": "Authentication failed due to server error"})
            response.set_cookie('session_token', '', expires=0)
            response.set_cookie('is_logged_in_indicator', '', expires=0)
            return response, 500
    return decorated_function

# --- Authentication Endpoint ---
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user authentication and authorization.
    Expects organizationId and firebaseIdToken in JSON body.
    Sets an HTTP-only session cookie upon success.
    Returns session token, user details, and menu items.
    """
    data = request.get_json()
    organization_id = data.get('organizationId')
    firebase_id_token = data.get('firebaseIdToken')
    
    if not organization_id or not firebase_id_token:
        return jsonify({"message": "Organization ID and Firebase ID Token are required"}), 400

    try:
        auth_service: AuthService = current_app.auth_service
        resource_service: ResourceService = current_app.resource_service 

        # Call authenticate_and_authorize, it returns user-specific auth data
        auth_data = auth_service.authenticate_and_authorize(organization_id, firebase_id_token)
        logger.debug(f"Authetication Context in login is {auth_data}");
        
        # Get menu items relevant to the organization.
        # Use organization_id from the request's input data, not auth_data, as per discussion.
        # menu_items = resource_service.get_menu_items(organization_id=organization_id) # Use request's organization_id

        # Get menu items relevant to the organization AND filtered by user roles
        menu_items = resource_service.get_menu_items(
            organization_id=organization_id, 
            user_roles=auth_data['roles'],
            user_id=auth_data['userId'] # Pass userId
        )
        logger.debug(f"MENUITEMS {menu_items}")

        agency_org_id = auth_data.get('agencyOrgId') # Get the agency/parent org ID
        
        

        response = jsonify({
            "message": "Login successful",
            "user": { # Basic user info for UI
                "uid": auth_data['uid'],
                "userId": auth_data['userId'],
                "email": auth_data['email'],
                "organizationId": organization_id, # Use organization_id from input
                "organizationType": auth_data['organizationType'], # NEW: Include org type in response
                "parentOrgId": agency_org_id, # CORRECTED: Use camelCase for consistency with token and status endpoint
                "roles": auth_data['roles'] 
            },
            "menuItems": menu_items 
        })
        
        cookie_max_age_seconds = int(timedelta(hours=12).total_seconds())

        response.set_cookie(
            'session_token',
            auth_data['sessionToken'], 
            httponly=True,
            samesite='Lax', 
            secure=current_app.config.get('FLASK_ENV') == 'production',
            max_age=cookie_max_age_seconds,
            path='/' 
        )
        logger.info(f"Session token cookie set for organization: {organization_id}")
        if agency_org_id is None:
            agency_org_id   =   organization_id
            
        logger.info(f"agencyOrgId {agency_org_id}")    
        response.set_cookie(
            'is_logged_in_indicator',
            'true', 
            samesite='Lax',
            secure=current_app.config.get('FLASK_ENV') == 'production', 
            max_age=cookie_max_age_seconds,
            path='/'
        )
        logger.info("is_logged_in_indicator cookie set.")

        # NEW: Set parentOrgId cookie if it exists
        if agency_org_id:
            response.set_cookie(
                'parentOrgId',
                agency_org_id,
                samesite='Lax',
                secure=current_app.config.get('FLASK_ENV') == 'production',
                max_age=cookie_max_age_seconds,
                path='/'
            )
            logger.info(f"parentOrgId cookie set with value: {agency_org_id}")

        return response, 200

    except ValueError as e:
        logger.warning(f"Login failed: {e}")
        return jsonify({"message": str(e)}), 401 
    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {e}", exc_info=True)
        return jsonify({"message": "Internal server error during login"}), 500

# --- Health check endpoint ---
@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Public health check endpoint for AWS ALB"""
    return jsonify({"status": "ok"}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clears the session cookies."""
    response = jsonify({"message": "Logged out successfully"})
    response.set_cookie('session_token', '', expires=0) 
    response.set_cookie('parentOrgId', '', expires=0)
    response.set_cookie('is_logged_in_indicator', '', expires=0)
    logger.info("Session cookies cleared.")
    return response, 200

@auth_bp.route('/status', methods=['GET']) 
@auth_required
def session_status():
    uid = getattr(g, 'firebase_uid', None)
    organization_id = getattr(g, 'organization_id', None)
    organization_type = getattr(g, 'organization_type', None) # NEW: Get from g
    parent_org_id = getattr(g, 'parent_org_id', None) # NEW: Get from g
    db_user_id = getattr(g, 'user_id', None)
    user_roles = getattr(g, 'user_roles', []) 

    if uid and organization_id:
        return jsonify({
            "isAuthenticated": True, 
            "firebaseUid": uid, 
            "userId": db_user_id,
            "organizationId": organization_id,
            "organizationType": organization_type, # NEW: Return in status
            "parentOrgId": parent_org_id, # NEW: Return in status
            "roles": user_roles 
        }), 200
    else:
        return jsonify({"isAuthenticated": False, "message": "Session invalid or context not found"}), 401
    
    
# NEW ENDPOINT: Register New User
@auth_bp.route('/register/new', methods=['POST'])
def register_new_user():
    """
    API endpoint to register a new user and associate them with an organization.
    Input: fullName, organizationName, email, firebaseIdToken, organizationId.
    """
    data = request.get_json()
    full_name = data.get('fullName')
    organization_name = data.get('organizationName')
    email = data.get('email')
    firebase_id_token = data.get('firebaseIdToken')
    organization_id = data.get('organizationId') # CRITICAL FIX: Get organizationId from request

    if not all([full_name, organization_name, email, firebase_id_token, organization_id]): # Validate all fields
        return jsonify({"error": "All fields (fullName, organizationName, email, firebaseIdToken, organizationId) are required"}), 400

    try:
        register_user_service: RegisterUserService = current_app.register_user_service
        
        registration_result = register_user_service.register_new_user(
            full_name=full_name,
            organization_name=organization_name,
            email=email,
            firebase_id_token=firebase_id_token,
            organization_id=organization_id # CRITICAL FIX: Pass organization_id
        )
        
        return jsonify(registration_result), 201 
    except ValueError as ve:
        logger.error(f"Registration validation error: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 400
    except RuntimeError as re: 
        logger.error(f"Registration processing error: {re}", exc_info=True)
        return jsonify({"error": str(re)}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred during user registration: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500