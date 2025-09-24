# routes/user_management_routes.py

from flask import Blueprint, request, jsonify, Response, current_app, g
import logging

from auth.auth_routes import auth_required 
from services.resource_service import ResourceService

user_management_bp = Blueprint('user_management_bp', __name__)

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

@user_management_bp.route('/v1/menu_items', methods=['GET'])
@auth_required # Secure this endpoint
def get_menu_items():
    """
    API endpoint to get a list of menu items.
    Retrieves menus relevant to the authenticated user's organization (or global ones).
    """
    logger.info(f"Authenticated user (DB ID: {g.user_id}, Firebase UID: {g.firebase_uid}) from org {g.organization_id} requesting menu items.")

    try:
        resource_service: ResourceService = current_app.resource_service
        
        # Pass the organization_id from the authenticated context (g)
        menu_items = resource_service.get_menu_items(organization_id=g.organization_id)
        
        return jsonify({"menuItems": menu_items}), 200
    except Exception as e:
        logger.error(f"Error getting menu items: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred while fetching menu items: {str(e)}"}), 500