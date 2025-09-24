# services/file_task_executor_service.py

import logging
import os
import io
import tempfile
import zipfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple, IO # Added IO for BytesIO type hint

# Assuming psutil is installed for optimal thread count
try:
    import psutil
    USE_PSUTIL = True
except ImportError:
    USE_PSUTIL = False

# Import services needed for processing individual resumes
from services.profile_management_service import ProfileManagementService 
from services.file_storage_service import FileStorageService
from database.bulk_profile_upload_repository import BulkProfileUploadRepository
# NEW: Import services and repositories for matching
from services.matching_engine_service import MatchingEngineService
from database.user_repository import UserRepository


logger = logging.getLogger(__name__)


class FileTaskExecutorService:
    """
    Executes long-running file processing tasks in the background.
    Responsible for retrieving files from storage, unzipping,
    and processing individual files in parallel.
    """

    def __init__(self,
                 profile_management_service: ProfileManagementService,
                 file_storage_service: FileStorageService,
                 bulk_profile_upload_repository: BulkProfileUploadRepository,
                 matching_engine_service: MatchingEngineService,
                 user_repository: UserRepository):
        self.profile_management_service = profile_management_service
        self.file_storage_service = file_storage_service
        self.bulk_profile_upload_repository = bulk_profile_upload_repository
        self.matching_engine_service = matching_engine_service
        self.user_repository = user_repository
        logger.info("FileTaskExecutorService initialized.")

    def execute_bulk_processing_task(self,
                                     zip_storage_path: str, # Path/URI to the stored ZIP file
                                     user_id: int,
                                     organization_id: str,
                                     job_id: int,
                                     upload_id: str, # The UUID from the tracking table
                                     file_name: Optional[str] = "uploaded_zip.zip",
                                     use_match_ai_client_v2: bool = False,
                                     max_threads: Optional[int] = None) -> Dict[str, Any]:
        """
        Internal method to execute the actual bulk processing of a zip file from storage.
        This is designed to be run in a separate thread/process.
        """
        logger.info(f"Executor: Starting bulk processing task for ZIP '{file_name}' from '{zip_storage_path}'.")

        temp_extract_dir = None
        all_processing_results = [] # To collect results for each processed file
        
        try:
            # 1. Retrieve the zip file from permanent storage as a BytesIO stream
            logger.info(f"Executor: Retrieving zip file from storage: {zip_storage_path}")
            zip_file_stream = self.file_storage_service.get_file_stream(zip_storage_path)

            # 2. Unzip the file to a temporary local directory
            temp_extract_dir = tempfile.mkdtemp()
            extracted_file_paths = self._unzip_file_from_stream(zip_file_stream, temp_extract_dir)
            
            if not extracted_file_paths:
                raise ValueError("No valid files found in the ZIP archive.")

            # 3. Determine optimal thread count for parallel processing
            if max_threads is None:
                max_threads = self._get_optimal_thread_count()

            # 4. Process individual files in parallel
            logger.info(f"Executor: Starting thread pool with max {max_threads} threads for {len(extracted_file_paths)} files.")
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(self._process_single_resume_for_bulk, fp, user_id, organization_id, job_id, upload_id, use_match_ai_client_v2) 
                    for fp in extracted_file_paths
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result() 
                        all_processing_results.append(result)
                    except Exception as e:
                        logger.error(f"Executor: Error getting result from future in bulk processing: {e}", exc_info=True)
                        all_processing_results.append({"status": "error", "file_name": "unknown_file_in_zip", "error_message": str(e)})

            logger.info(f"Executor: Bulk processing task for '{file_name}' completed. Processed {len(extracted_file_paths)} files.")
            
            # NEW: Update status to 'completed'
            self.bulk_profile_upload_repository.update_upload_status(upload_id, 'completed')

            return {"status": "completed", "total_files": len(extracted_file_paths), "results": all_processing_results}

        except Exception as e:
            logger.error(f"Executor: An error occurred during bulk file processing task: {e}", exc_info=True)
            # NEW: Update status to 'failed'
            self.bulk_profile_upload_repository.update_upload_status(upload_id, 'failed')
            return {"status": "failed", "error": str(e), "results": all_processing_results}
        finally:
            # Clean up temporary extracted files directory
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                try:
                    shutil.rmtree(temp_extract_dir)
                    logger.debug(f"Executor: Cleaned up extracted files directory: {temp_extract_dir}")
                except Exception as e:
                    logger.warning(f"Executor: Failed to remove extracted files directory {temp_extract_dir}: {e}", exc_info=True)
            
            # Optional: Delete the original ZIP file from permanent storage after processing
            # self.file_storage_service.delete_file(zip_storage_path)
            # logger.info(f"Executor: Deleted original ZIP file from storage: {zip_storage_path}")


    # --- Helper Methods (moved from previous BulkFileProcessorService) ---

    def _unzip_file_from_stream(self, zip_file_stream: io.BytesIO, extract_to: str) -> List[str]:
        """Unzips the ZIP file stream and returns a list of extracted file paths."""
        file_paths = []
        try:
            zip_file_stream.seek(0)
            with zipfile.ZipFile(zip_file_stream, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                for root, _, files in os.walk(extract_to):
                    for file in files:
                        if os.path.isfile(os.path.join(root, file)) and not file.startswith('.'):
                            file_paths.append(os.path.join(root, file))
            logger.info(f"Unzipped {len(file_paths)} files to '{extract_to}'.")
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file format.")
            raise ValueError("Uploaded file is not a valid ZIP archive.")
        except Exception as e:
            logger.error(f"Error unzipping file: {e}", exc_info=True)
            raise RuntimeError(f"Failed to unzip file: {str(e)}")
        return file_paths

    def _process_single_resume_for_bulk(self, file_path: str, user_id: int, organization_id: str, job_id: int, upload_id: str, use_match_ai_client_v2: bool) -> Dict[str, Any]:
        """
        Helper method to process a single resume file (from a bulk upload)
        and return its status and processed data. This is executed by worker threads.
        """
        file_name = os.path.basename(file_path)
        logger.debug(f"[Bulk Worker] Processing {file_name} (Path: {file_path}) for batch {upload_id}")
        try:
            # --- Step 1: Process and save the resume profile ---
            if use_match_ai_client_v2:
                processed_data = self.profile_management_service.process_uploaded_resume_v3( # Calls V3 method
                    file_path=file_path,
                    user_id=user_id,
                    organization_id=organization_id,
                    # job_id=job_id, # This parameter does not exist on the target method
                    file_name=file_name,
                    filebatchid=upload_id # Pass the upload_id as filebatchid
                )
            else:
                with open(file_path, 'rb') as f:
                    file_stream = io.BytesIO(f.read())
                processed_data = self.profile_management_service.process_uploaded_resume_v1( # Calls V1 method
                    file_stream=file_stream,
                    user_id=user_id,
                    organization_id=organization_id,
                    file_name=file_name,
                    filebatchid=upload_id # Pass the upload_id as filebatchid
                )
            
            logger.info(f"[Bulk Worker] Successfully processed: {file_name} (DB ID: {processed_data.get('db_id', 'N/A')})")

            # --- Step 2: Perform matching if profile was created successfully ---
            profile_id = processed_data.get('db_id')
            if profile_id:
                try:
                    # Fetch user roles required by the matching service for authorization checks
                    # user_roles = self.user_repository.get_user_roles_by_id(user_id)
                    # logger.info(f"[Bulk Worker] Initiating match for profile {profile_id} against job {job_id}.")
                    
                    self.matching_engine_service.perform_match(
                        job_id=job_id,
                        profile_id=profile_id,
                        current_user_id=user_id,
                        current_org_id=organization_id,
                        current_user_roles=''
                    )
                    logger.info(f"[Bulk Worker] Match successfully performed for profile {profile_id}.")
                except Exception as match_error:
                    logger.error(f"[Bulk Worker] Failed to perform match for profile {profile_id} against job {job_id}: {match_error}", exc_info=True)
                    # Do not fail the entire resume processing, just log the matching error.

            return {"status": "success", "file_name": file_name, "data": processed_data}
        except Exception as e:
            logger.error(f"[Bulk Worker] Error processing {file_name}: {e}", exc_info=True)
            return {"status": "error", "file_name": file_name, "error_message": str(e)}

    def _get_optimal_thread_count(self, max_cap: int = 16) -> int:
        """Determine the optimal thread count based on system resources."""
        cores = os.cpu_count() or 4
        if USE_PSUTIL:
            available_gb = psutil.virtual_memory().available / (1024 ** 3)
            mem_based_threads = int(available_gb * 0.5) 
            thread_count = min(mem_based_threads, cores * 2, max_cap)
            if thread_count < 1: thread_count = 1 
        else:
            thread_count = min(cores * 2, max_cap)
        logger.info(f"Auto-selected max_threads: {thread_count}")
        return thread_count