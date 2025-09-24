# auth/firebase_manager.py
import logging
from firebase_admin import credentials, initialize_app, auth
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_firebase_app_initialized = False

def initialize_firebase_app(service_account_path):
    """Initializes the Firebase Admin SDK."""
    global _firebase_app_initialized
    if not _firebase_app_initialized:
        try:
            if not os.path.exists(service_account_path):
                logger.error(f"Firebase service account key not found at: {service_account_path}")
                raise FileNotFoundError(f"Firebase service account key not found at: {service_account_path}")

            cred = credentials.Certificate(service_account_path)
            initialize_app(cred)
            _firebase_app_initialized = True
            logger.info("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            logger.critical(f"FATAL: Error initializing Firebase Admin SDK: {e}", exc_info=True)
            raise
    else:
        logger.info("Firebase Admin SDK already initialized.")

def verify_firebase_id_token(id_token):
    """Verifies a Firebase ID token."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        logger.debug(f"Firebase ID Token verified for UID: {decoded_token.get('uid')}")
        return decoded_token
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID Token provided.")
        raise
    except Exception as e:
        logger.error(f"Error verifying Firebase ID Token: {e}", exc_info=True)
        raise