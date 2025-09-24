import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_for_dev'
    SECRET_KEY = os.environ.get('APP_SECRET_KEY', 'your_super_secret_flask_key_change_me_in_production') # Use APP_SECRET_KEY for Flask

    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    
    # PostgreSQL Database URI
    # Format: postgresql+psycopg2://user:password@host:port/database_name
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
                              "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/resume_db"
    # SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/resume_db"

    # Firebase Service Account Path
    FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'profileauth-90a2f-firebase-adminsdk-fbsvc-10ed93c6a4.json')

    # Paths for prompt templates relative to the project root
    PROMPT_SCHEMA_PATH = 'prompt_templates/resume_schema.json'
    PROMPT_TEMPLATE_PATH = 'prompt_templates/resume_parser_prompt.txt'
    
    # NEW: PostgreSQL Connection Pool Configuration
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 10))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600)) # In seconds (1 hour)
    DB_POOL_PRE_PING = os.environ.get('DB_POOL_PRE_PING', 'True').lower() == 'true'
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', 30))
    DB_CONNECT_RETRIES = int(os.environ.get('DB_CONNECT_RETRIES', 3))
    DB_RETRY_DELAY_SECONDS = int(os.environ.get('DB_RETRY_DELAY_SECONDS', 5))   
    
  # NEW: AWS S3 Configuration (for production/cloud storage)
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1') # e.g., 'us-east-1'
    AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME', 'your-aws-s3-bucket') # CHANGE THIS IN PRODUCTION
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY usually come from env vars or IAM roles
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = False
    FLASK_ENV = 'development'
  # Allow CORS from any origin in dev for frontend development
    CORS_HEADERS = 'Content-Type'
    CORS_RESOURCES = {r"/api/*": {"origins": "*"}}    
    LOCAL_STORAGE_PATH = 'uploaded_files_dev' 
    
    # For development, you might use smaller pools or more aggressive recycle
    # DB_POOL_SIZE = 5
    # DB_MAX_OVERFLOW = 5
    # DB_POOL_RECYCLE = 300 # 5 minutes for dev
    # DB_CONNECT_RETRIES = 1 # Less retries in dev    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'
    # Add more robust logging, error handling, etc. for production
   # IMPORTANT: In production, specify your frontend's exact domain for CORS
    CORS_HEADERS = 'Content-Type'
    CORS_RESOURCES = {r"/api/*": {"origins": "http://hirelyst.s3-website-us-east-1.amazonaws.com"}} # CHANGE THIS IN PRODUCTION
    
    LOCAL_STORAGE_PATH = 'uploaded_files_prod' 
    # AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME_PROD') # Can be separate env var for prod
    # AWS_REGION = os.environ.get('AWS_REGION_PROD')    
    
    # Ensure HTTPS is enforced in production    
    # Production values (can be overridden by environment variables)
    # DB_POOL_SIZE = 20
    # DB_MAX_OVERFLOW = 20
    # DB_POOL_RECYCLE = 3600
    # DB_POOL_PRE_PING = True
    # DB_POOL_TIMEOUT = 60
    # DB_CONNECT_RETRIES = 5
    # DB_RETRY_DELAY_SECONDS = 10
    
# Mapping for easy access to configs
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}