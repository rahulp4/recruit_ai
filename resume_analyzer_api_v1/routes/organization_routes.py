# routes/organization_routes.py

from flask import Blueprint, request, jsonify, Response, current_app, g
import logging

from auth.auth_routes import auth_required # Import the decorator
from services.organization_management_service import OrganizationManagementService # Import new service

org_bp = Blueprint('org_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

@org_bp.route('/create', methods=['POST'])
@auth_required
def create_organization():
    """
    API endpoint to create a new organization.
    Requires 'org:create' permission.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} attempting to create organization.")
    
    data = request.get_json()
    org_id = data.get('id')
    name = data.get('name')
    organization_type = data.get('organizationType') # Optional

    if not org_id or not name:
        return jsonify({"error": "Organization ID and Name are required"}), 400

    try:
        org_management_service: OrganizationManagementService = current_app.organization_management_service
        new_org = org_management_service.create_organization(
            org_id=org_id,
            name=name,
            organization_type=organization_type,
            current_user_id=g.user_id,
            current_user_roles=g.user_roles
        )
        return jsonify({"message": "Organization created successfully", "organization": new_org}), 201
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403 # Forbidden
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400 # Bad Request
    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while creating organization"}), 500

@org_bp.route('/<string:org_id>', methods=['GET'])
@auth_required
def get_organization(org_id: str):
    """
    API endpoint to retrieve details of a specific organization.
    Requires 'org:read' permission for the specific org or 'org:list' globally for admins.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} requesting details for org {org_id}.")
    try:
        org_management_service: OrganizationManagementService = current_app.organization_management_service
        org_details = org_management_service.get_organization(
            org_id=org_id,
            current_user_id=g.user_id,
            current_org_id=g.organization_id, # User's own org
            current_user_roles=g.user_roles
        )
        if org_details:
            return jsonify(org_details), 200
        return jsonify({"message": "Organization not found or not authorized"}), 404
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        logger.error(f"Error getting organization {org_id} details: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while fetching organization details"}), 500


@org_bp.route('/v1/accessible_list', methods=['GET'])
@auth_required
def list_accessible_organizations():
    """
    API endpoint to get a list of organizations accessible to the logged-in user's organization.
    This includes their own org and, if an Agency, their affiliated client orgs.
    Requires 'org:list_accessible' permission.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} requesting list of accessible organizations.")
    
    try:
        org_management_service: OrganizationManagementService = current_app.organization_management_service
        
        accessible_orgs = org_management_service.list_accessible_organizations(
            current_user_id=g.user_id,
            current_org_id=g.organization_id,
            current_user_roles=g.user_roles # Pass roles for permission check
        )
        return jsonify({"organizations": accessible_orgs}), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403 # Forbidden
    except Exception as e:
        logger.error(f"Error listing accessible organizations: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while fetching accessible organizations"}), 500


@org_bp.route('/<string:org_id>', methods=['PUT'])
@auth_required
def update_organization(org_id: str):
    """
    API endpoint to update an existing organization.
    Requires 'org:update' permission for the specific org.
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} attempting to update org {org_id}.")
    
    updates = request.get_json()
    if not updates:
        return jsonify({"error": "No update data provided"}), 400

    try:
        org_management_service: OrganizationManagementService = current_app.organization_management_service
        is_updated = org_management_service.update_organization(
            org_id=org_id,
            updates=updates,
            current_user_id=g.user_id,
            current_org_id=g.organization_id,
            current_user_roles=g.user_roles
        )
        if is_updated:
            return jsonify({"message": f"Organization {org_id} updated successfully"}), 200
        return jsonify({"message": f"Organization {org_id} not found or no changes made"}), 404
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.error(f"Error updating organization {org_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while updating organization"}), 500

@org_bp.route('/list', methods=['GET'])
@auth_required
def list_organizations():
    """
    API endpoint to get a list of all organizations.
    Requires 'org:list' permission (global permission for admins).
    """
    logger.info(f"User {g.user_id} ({g.firebase_uid}) from org {g.organization_id} requesting list of organizations.")
    
    filters = {}
    # Example filters from query params
    if 'is_active' in request.args:
        filters['is_active'] = request.args['is_active'].lower() == 'true'
    if 'organization_type' in request.args:
        filters['organization_type'] = request.args['organization_type']
    if 'name_like' in request.args:
        filters['name_like'] = request.args['name_like']

    try:
        org_management_service: OrganizationManagementService = current_app.organization_management_service
        orgs = org_management_service.list_organizations(
            filters=filters,
            current_user_id=g.user_id,
            current_user_roles=g.user_roles
        )
        return jsonify({"organizations": orgs}), 200
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 403
    except Exception as e:
        logger.error(f"Error listing organizations: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while listing organizations"}), 500