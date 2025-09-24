# services/file_storage_service.py

import logging
import os
import uuid # For unique filenames
import io # For BytesIO
from typing import Tuple, Dict, Any
from werkzeug.datastructures import FileStorage # For type hinting MultipartFile
from google.cloud import storage # Import Google Cloud Storage
import boto3 # NEW: Import boto3 for AWS S3

logger = logging.getLogger(__name__)

class FileStorageService:
    """
    Handles storage of uploaded files to local disk in development
    and Google Cloud Storage/AWS S3 in production.
    """
    def __init__(self, app_config: Dict[str, Any], app_env: str):
        self.app_config = app_config
        self.app_env = app_env
        self.local_storage_path = app_config['LOCAL_STORAGE_PATH']
        
        # GCS Config
        self.gcs_bucket_name = app_config.get('GCS_BUCKET_NAME')
        self.gcp_project_id = app_config.get('GCP_PROJECT_ID')

        # AWS S3 Config
        self.aws_region = app_config.get('AWS_REGION')
        self.aws_s3_bucket_name = app_config.get('AWS_S3_BUCKET_NAME')
        
        self.storage_client_gcs = None
        self.bucket_gcs = None
        self.s3_client = None
        self.s3_bucket = None

        if self.app_env == 'development':
            os.makedirs(self.local_storage_path, exist_ok=True) # Create local dir if not exists
            logger.info(f"FileStorageService initialized for DEVELOPMENT. Local path: {self.local_storage_path}")
        elif self.app_env == 'production':
            # Initialize GCS client if bucket name is provided
            if self.gcs_bucket_name and self.gcp_project_id:
                try:
                    self.storage_client_gcs = storage.Client(project=self.gcp_project_id)
                    self.bucket_gcs = self.storage_client_gcs.bucket(self.gcs_bucket_name)
                    logger.info(f"FileStorageService initialized for PRODUCTION with GCS Bucket: {self.gcs_bucket_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Google Cloud Storage client: {e}. GCS storage will not be available.", exc_info=True)
            
            # Initialize S3 client if bucket name and region are provided
            if self.aws_s3_bucket_name and self.aws_region:
                try:
                    self.s3_client = boto3.client('s3', region_name=self.aws_region)
                    self.s3_bucket = self.aws_s3_bucket_name # Store bucket name
                    logger.info(f"FileStorageService initialized for PRODUCTION with AWS S3 Bucket: {self.s3_bucket} in region {self.aws_region}")
                except Exception as e:
                    logger.warning(f"Failed to initialize AWS S3 client: {e}. S3 storage will not be available.", exc_info=True)
            
            if not self.storage_client_gcs and not self.s3_client:
                logger.critical("FileStorageService in PRODUCTION: Neither GCS nor S3 client initialized. File storage will fail.")
                # Depending on your policy, you might raise an error here to halt startup.
                # raise RuntimeError("No cloud storage configured for production.")

        else:
            raise ValueError(f"Unknown Flask environment: {self.app_env}")

    def save_file(self, file_stream: io.BytesIO, original_filename: str) -> Tuple[str, str]:
        """
        Saves the file stream to the configured storage.
        
        Args:
            file_stream: The BytesIO stream of the file.
            original_filename: The original name of the file (e.g., 'resume.docx').
            
        Returns:
            A tuple (storage_path, unique_filename_on_cloud).
            storage_path is the local file path or cloud storage URI (gs://bucket/object or s3://bucket/object).
            unique_filename_on_cloud is the name of the file as stored in cloud (UUID based).
        """
        # Create a unique filename to avoid collisions and provide a clean name for cloud storage
        unique_filename = f"{uuid.uuid4().hex}{os.path.splitext(original_filename)[1]}"
        
        if self.app_env == 'development':
            file_path = os.path.join(self.local_storage_path, unique_filename)
            try:
                # Ensure local directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Rewind stream before saving
                file_stream.seek(0)
                with open(file_path, 'wb') as f:
                    f.write(file_stream.read())
                logger.info(f"File saved locally to: {file_path}")
                return file_path, unique_filename
            except Exception as e:
                logger.error(f"Failed to save file locally: {e}", exc_info=True)
                raise
        elif self.app_env == 'production':
            if self.s3_client: # Prioritize S3 if configured
                try:
                    s3_object_key = f"uploads/{unique_filename}" # Use a folder structure in S3
                    file_stream.seek(0) # Rewind stream before uploading
                    self.s3_client.upload_fileobj(file_stream, self.s3_bucket, s3_object_key)
                    s3_uri = f"s3://{self.s3_bucket}/{s3_object_key}"
                    logger.info(f"File uploaded to AWS S3: {s3_uri}")
                    return s3_uri, unique_filename
                except Exception as e:
                    logger.error(f"Failed to upload file to AWS S3 bucket {self.s3_bucket}: {e}", exc_info=True)
                    # Fallback to GCS if S3 fails and GCS is configured
                    if self.bucket_gcs:
                        logger.warning("Attempting to fallback to GCS due to S3 failure.")
                    else:
                        raise RuntimeError(f"Failed to save file to S3, and no GCS fallback: {str(e)}")
            
            if self.bucket_gcs: # Fallback to GCS if S3 not configured or failed
                try:
                    gcs_blob_name = f"uploads/{unique_filename}" # Use a folder structure in GCS
                    blob = self.bucket_gcs.blob(gcs_blob_name)
                    file_stream.seek(0) # Rewind stream before uploading
                    blob.upload_from_file(file_stream)
                    gcs_uri = f"gs://{self.gcs_bucket_name}/{gcs_blob_name}"
                    logger.info(f"File uploaded to GCS: {gcs_uri}")
                    return gcs_uri, unique_filename
                except Exception as e:
                    logger.error(f"Failed to upload file to GCS bucket {self.gcs_bucket_name}: {e}", exc_info=True)
                    raise RuntimeError(f"Failed to save file to GCS: {str(e)}")
            
            raise RuntimeError("No cloud storage configured or available for production environment.")
        return "", "" # Should not be reached

    def get_file_stream(self, storage_path: str) -> io.BytesIO:
        """
        Retrieves a file as a BytesIO stream from storage.
        """
        file_stream = io.BytesIO()
        if self.app_env == 'development':
            if not os.path.exists(storage_path):
                raise FileNotFoundError(f"Local file not found: {storage_path}")
            with open(storage_path, 'rb') as f:
                file_stream.write(f.read())
        elif self.app_env == 'production':
            if storage_path.startswith("s3://") and self.s3_client:
                bucket_name, object_key = storage_path[5:].split('/', 1)
                self.s3_client.download_fileobj(bucket_name, object_key, file_stream)
            elif storage_path.startswith("gs://") and self.bucket_gcs:
                bucket_name, blob_name = storage_path[5:].split('/', 1)
                blob = self.storage_client_gcs.bucket(bucket_name).blob(blob_name)
                blob.download_to_file(file_stream)
            else:
                raise ValueError(f"Invalid storage URI format or client not configured: {storage_path}")
        file_stream.seek(0) # Rewind to the beginning
        return file_stream

    def delete_file(self, storage_path: str):
        """
        Deletes a file from storage.
        """
        if self.app_env == 'development':
            if os.path.exists(storage_path):
                try:
                    os.remove(storage_path)
                    logger.info(f"File deleted locally: {storage_path}")
                except Exception as e:
                    logger.error(f"Failed to delete local file {storage_path}: {e}", exc_info=True)
        elif self.app_env == 'production':
            if storage_path.startswith("s3://") and self.s3_client:
                try:
                    bucket_name, object_key = storage_path[5:].split('/', 1)
                    self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
                    logger.info(f"File deleted from S3: {storage_path}")
                except Exception as e:
                    logger.error(f"Failed to delete S3 object {storage_path}: {e}", exc_info=True)
            elif storage_path.startswith("gs://") and self.bucket_gcs:
                try:
                    bucket_name, blob_name = storage_path[5:].split('/', 1)
                    blob = self.storage_client_gcs.bucket(bucket_name).blob(blob_name)
                    blob.delete()
                    logger.info(f"File deleted from GCS: {storage_path}")
                except Exception as e:
                    logger.error(f"Failed to delete GCS blob {storage_path}: {e}", exc_info=True)
            else:
                logger.warning(f"Could not delete file: Invalid storage URI or client not configured for {storage_path}")