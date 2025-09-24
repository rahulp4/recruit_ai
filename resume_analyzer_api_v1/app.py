
import os
import logging
from flask import Flask
from config import config_by_name # Import the config mapping
from database.postgres_manager import init_db_manager # Import the database manager initializer
from flask_cors import CORS # Make sure CORS is imported

# Import services and repository
from services.resume_parser_service import ResumeParserService
from services.data_analyzer_service import DataAnalyzerService
from services.embedding_service import EmbeddingService
from database.profile_repository import ProfileRepository
from database.organization_repository import OrganizationRepository
from database.user_repository import UserRepository
from database.bulk_profile_upload_repository import BulkProfileUploadRepository
from database.resource_repository import ResourceRepository # Already added
from database.job_description_repository import JobDescriptionRepository
from database.permission_repository import PermissionRepository 
from database.agency_info_repository import AgencyInfoRepository # NEW: Import AgencyInfoRepository

# Import auth components
from auth.firebase_manager import initialize_firebase_app
from auth.auth_service import AuthService
from auth.auth_routes import auth_bp
from routes.profile_routes import profile_bp # Import the profile blueprint
from routes.user_management_routes import user_management_bp
# NEW: Import MatchAIClient for initialization
from matchai import MatchAIClient # Ensure this path is correct for your MatchAIClient library
# If MatchAIClient lives in a subfolder like 'matchai/matchai.py', it would be:
# from matchai.matchai import MatchAIClient 
# Assuming 'matchai' is a top-level package next to 'services', 'routes' etc.
from services.profile_management_service import ProfileManagementService
from services.resource_service import ResourceService # Already added
from services.jd_parser_service import JDParserService # Already added
from services.organization_management_service import OrganizationManagementService
from services.job_description_management_service import JobDescriptionManagementService # NEW: Import JD Management Service
from services.matching_engine_service import MatchingEngineService # NEW: Import MatchingEngineService
from database.job_profile_match_repository import JobProfileMatchRepository # NEW: Import JobProfileMatchRepository
from services.bulk_file_processor_service import BulkFileProcessorService # Already imported



# Import new routes
from routes.user_management_routes import user_management_bp 
from routes.job_description_routes import jd_bp # Already added
from routes.organization_routes import org_bp # NEW: Import Organization Blueprint
# NEW: Import plugin loading system
from plugins import load_all_plugins # Assuming 'plugins' is a top-level package
from plugin_registry import PLUGIN_REGISTRY # Assuming PLUGIN_REGISTRY is here
from routes.matching_routes import match_bp # NEW: Import Matching Routes Blueprint
from sentence_transformers import SentenceTransformer, util
# Configure logging for the main app
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from services.file_storage_service import FileStorageService
from services.file_task_executor_service import FileTaskExecutorService # NEW: Import FileTaskExecutorService

from services.register_user_service import RegisterUserService # NEW: Import RegisterUserService
import google.generativeai as genai
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s'
)


logger = logging.getLogger(__name__)



def create_app(config_name=None):
    """Factory function to create the Flask app."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize CORS
    # For development, allow specific origin.
    # For production, this should be your actual frontend domain.
    if app.config['FLASK_ENV'] == 'development':
        # CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
        # CORS(app, resources={r"*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

        # CORS(
        #     app,
        #     origins=["http://localhost:3000"],
        #     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        #     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Custom-Upload-Request"], # <<<<< ADD YOUR CUSTOM HEADER
        #     supports_credentials=True # This is crucial
        # )
        CORS(
        app,
        origins=["http://localhost:3000"],  # Explicitly allow your React app's origin
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Ensure OPTIONS and POST are here
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"], # Add common headers, X-Requested-With is sometimes sent
        supports_credentials=True, # THIS IS CRUCIAL
        expose_headers=["Content-Length", "X-My-Custom-Header"] # Expose any custom headers you might send back
        )
        logger.info("CORS initialized for development (origin: http://localhost:3000)")
    else:
        # Example for production - get allowed origins from config
        #allowed_origins = app.config.get('CORS_ALLOWED_ORIGINS', [])
        #CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
        
        # For now, let's keep it permissive for testing if you deploy to a non-dev env without specific origin config
        # CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True) # Be more specific in production
        CORS(app, resources={r"/api/*": {"origins": ["https://app.hyreassist.co"]}}, supports_credentials=True)

        # CORS(
        # app,
        # origins=["http://hirelyst.s3-website-us-east-1.amazonaws.com"],  # Explicitly allow your React app's origin
        # methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Ensure OPTIONS and POST are here
        # allow_headers=["Content-Type", "Authorization", "X-Requested-With"], # Add common headers, X-Requested-With is sometimes sent
        # supports_credentials=True, # THIS IS CRUCIAL
        # expose_headers=["Content-Length", "X-My-Custom-Header"] # Expose any custom headers you might send back
        # )
        logger.info("CORS initialized for production (hire: *) - Consider restricting in production.")


    logger.info(f"App created with config: {config_name}")

    # Initialize Firebase Admin SDK
    initialize_firebase_app(app.config['FIREBASE_SERVICE_ACCOUNT_PATH'])

    # Initialize PostgreSQL Database Manager
    init_db_manager(app)
    
    
    # NEW: Initialize Gemini model ONCE
    try:
        genai.configure(api_key=app.config['GOOGLE_API_KEY'])
        app.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        logger.critical("!!!!!!! Gemini model 'gemini-2.5-flash' loaded ONCE in app.py !!!!!!!")
    except Exception as e:
        logger.error(f"FATAL: Failed to load Gemini model at startup: {e}", exc_info=True)
        raise RuntimeError("Application startup failed: Could not load Gemini model.")

    # Initialize repositories
    app.profile_repository = ProfileRepository()
    app.organization_repository = OrganizationRepository()
    app.user_repository = UserRepository()
    app.resource_repository = ResourceRepository() # Initialize ResourceRepository
    app.jd_repository = JobDescriptionRepository() # NEW: Initialize JobDescriptionRepository
    app.permission_repository = PermissionRepository() 
    app.agency_info_repository = AgencyInfoRepository() # NEW: Initialize AgencyInfoRepository
    app.jpm_repo = JobProfileMatchRepository() # NEW: Initialize JobProfileMatchRepository

    app.bulk_profile_upload_repository = BulkProfileUploadRepository()

    # Initialize services and attach them to the app context
    app.resume_parser_service = ResumeParserService(api_key=app.config['GOOGLE_API_KEY'])
    app.data_analyzer_service = DataAnalyzerService()
    app.embedding_service = EmbeddingService(api_key=app.config['GOOGLE_API_KEY'])
    
    app.auth_service = AuthService(
        org_repo=app.organization_repository,
        user_repo=app.user_repository,
        agency_info_repo=app.agency_info_repository,
        app_secret_key=app.config['SECRET_KEY'] # SECRET_KEY is used as APP_SECRET_KEY
    )
    
    # NEW: Initialize ResourceService
    app.resource_service = ResourceService( # ADD THIS BLOCK
        resource_repository=app.resource_repository
    )
    
    app.jd_parser_service = JDParserService(
        api_key=app.config['GOOGLE_API_KEY'],
        schema_path='prompt_templates/jd_schema.json', 
        prompt_template_path='prompt_templates/jd_parser_prompt.txt' 
    )
    # NEW: Initialize JobDescriptionManagementService
    app.jd_management_service = JobDescriptionManagementService( # NEW
        jd_parser_service=app.jd_parser_service,
        embedding_service=app.embedding_service,
        jd_repository=app.jd_repository,
     # CRITICAL FIX: Add org_repo and perm_repo here
        org_repo=app.organization_repository, # NEW
        perm_repo=app.permission_repository   # NEW        
    )
    
    

    # NEW: Initialize FileStorageService
    app.file_storage_service = FileStorageService( # NEW
        app_config=app.config,
        app_env=app.config['FLASK_ENV']
    )
        
    # NEW: Initialize ProfileManagementService, passing all its dependencies
    app.profile_management_service = ProfileManagementService(
        resume_parser_service=app.resume_parser_service,
        data_analyzer_service=app.data_analyzer_service,
        embedding_service=app.embedding_service,
        profile_repository=app.profile_repository,
        organization_repository=app.organization_repository
    )
    
    # NEW: Initialize OrganizationManagementService
    app.organization_management_service = OrganizationManagementService( # NEW
        org_repo=app.organization_repository,
        perm_repo=app.permission_repository,
        agency_info_repo=app.agency_info_repository

    )
    
    # NEW: Initialize RegisterUserService
    app.register_user_service = RegisterUserService( # Initialize RegisterUserService
        org_repo=app.organization_repository,
        user_repo=app.user_repository,
        perm_repo=app.permission_repository,
        auth_service=app.auth_service
    )

    # OPTIMIZATION: Don't load the model here - use lazy loading instead
    # This prevents each Gunicorn worker from loading the model at startup
    # model_name="all-MiniLM-L6-v2"
    # model = SentenceTransformer(model_name)

  # Load plugins here, after core services are available (if plugins need them)
    load_all_plugins() # This function call will populate PLUGIN_REGISTRY
    logger.info(f"All plugins loaded. Total plugins: {len(PLUGIN_REGISTRY)}")

    # CRITICAL FIX: Retrieve the local matcher callable once after plugins are loaded
    local_matcher_callable = PLUGIN_REGISTRY.get('localmatcherv2') # Get it safely
    if local_matcher_callable is None:
        logger.critical("!!!!!!! ERROR: 'localmatcher_match_function' not found in PLUGIN_REGISTRY. Matching engine will not work. !!!!!!!")
        # Decide if you want to raise an exception here to halt startup, or just log.
        # For production, probably raise.
        # raise RuntimeError("'localmatcher_match_function' plugin not found.") # Example: halt startup

    
    # NEW: Initialize MatchingEngineService
    app.matching_engine_service = MatchingEngineService( # NEW
        jd_repo=app.jd_repository,
        profile_repo=app.profile_repository,
        perm_repo=app.permission_repository,
        local_matcher_callable=local_matcher_callable, # CRITICAL FIX: Pass the callable
        model=None,  # OPTIMIZATION: Pass None, model will be loaded lazily when needed
        jpm_repo=app.jpm_repo, # NEW: Pass JobProfileMatchRepository
        org_repo=app.organization_repository, # CRITICAL FIX: Pass app.organization_repository
        modelgen=app.gemini_model, # CRITICAL FIX: Pass the Gemini model instance
    )
    
    # NEW: Initialize FileTaskExecutorService with MatchingEngineService and UserRepository
    app.file_task_executor_service = FileTaskExecutorService(
        profile_management_service=app.profile_management_service,
        file_storage_service=app.file_storage_service,
        bulk_profile_upload_repository=app.bulk_profile_upload_repository,
        matching_engine_service=app.matching_engine_service,
        user_repository=app.user_repository
    )
    
    # NEW: Initialize BulkFileProcessorService and pass ProfileManagementService and FileStorageService to it
    app.bulk_file_processor_service = BulkFileProcessorService( # ADD THIS BLOCK
        profile_management_service=app.profile_management_service,
        file_storage_service=app.file_storage_service,
        file_task_executor_service=app.file_task_executor_service,
        bulk_profile_upload_repository=app.bulk_profile_upload_repository
    )
    
    # NEW: Initialize MatchAIClient and attach to app context
    # This requires GOOGLE_API_KEY for the MatchAIClient itself
    app.match_ai_client = MatchAIClient(api_key=app.config['GOOGLE_API_KEY'])
    
      # If MatchAIClient is used by ProfileManagementService, attach it internally
    if app.match_ai_client: # This check is good
        app.profile_management_service.set_match_ai_client(app.match_ai_client) 
        logger.info("MatchAIClient instance set in ProfileManagementService.")
        
    logger.info("MatchAIClient initialized and attached to app context.")
        
    logger.info("Services and Repositories initialized and attached to app context.")
    load_all_plugins()
    logger.info(f"All plugins loaded. Total plugins: {len(PLUGIN_REGISTRY)}") # CRITICAL FIX: Access as a dict

    # Add health check endpoint for memory optimization monitoring
    @app.route('/health/memory', methods=['GET'])
    def memory_health_check():
        """Health check endpoint to monitor memory optimization."""
        import os
        from services.model_manager import model_manager

        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            memory_mb = "psutil_not_available"

        return {
            'status': 'healthy',
            'worker_pid': os.getpid(),
            'memory_usage_mb': memory_mb,
            'sentence_transformer_loaded': model_manager.is_model_loaded(),
            'optimization': 'lazy_loading_enabled'
        }

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(user_management_bp, url_prefix='/api/user_management') # ADD THIS LINE
    app.register_blueprint(jd_bp, url_prefix='/api/jd') # Register JD Blueprint
    app.register_blueprint(org_bp, url_prefix='/api/organization') # NEW: Register Organization Blueprint
    app.register_blueprint(match_bp, url_prefix='/api/match') # NEW: Register Match Blueprint

    logger.info("Blueprints registered.")

    @app.route('/')
    def index():
        return "Resume Analyzer API is running!"

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=(os.getenv('FLASK_ENV', 'development') == 'development'))

# if __name__ == '__main__':
#     app = create_app(os.getenv('FLASK_ENV', 'development'))
#     # Ensure debug is True for development to see detailed errors
#     # Port can be different if 5000 is in use, but keep it consistent
#     app.run(host='0.0.0.0', port=8080, debug=(os.getenv('FLASK_ENV', 'development') == 'development'))