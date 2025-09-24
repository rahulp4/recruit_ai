# services/bulk_file_processor_service.py

import logging
import os
import io
import tempfile
import zipfile
import shutil
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import IO, List, Dict, Any, Tuple, Optional
from database.bulk_profile_upload_repository import BulkProfileUploadRepository

# Assuming psutil is installed for optimal thread count
try:
    import psutil
    USE_PSUTIL = True
except ImportError:
    USE_PSUTIL = False

from services.profile_management_service import ProfileManagementService # To call its single-file processing methods
from services.file_storage_service import FileStorageService # To retrieve files from storage
from services.file_task_executor_service import FileTaskExecutorService # NEW: Import FileTaskExecutorService

logger = logging.getLogger(__name__)


class BulkFileProcessorService:
    """
    Service to process a zip file containing multiple resumes in parallel.
    It takes a storage path (e.g., S3 URI or local path) of the ZIP file.
    """

    def __init__(self,
                 profile_management_service: ProfileManagementService,
                 file_storage_service: FileStorageService,
                 file_task_executor_service: FileTaskExecutorService,
                 bulk_profile_upload_repository: BulkProfileUploadRepository):
        self.profile_management_service = profile_management_service
        self.file_storage_service = file_storage_service
        self.file_task_executor_service = file_task_executor_service
        self.bulk_profile_upload_repository = bulk_profile_upload_repository
        logger.info("BulkFileProcessorService initialized.")
        self.result_queue = queue.Queue() # Queue to collect results from worker threads
        self.stop_event = threading.Event() # Event to signal daemon to stop

    def _unzip_file_from_stream(self, zip_file_stream: io.BytesIO, extract_to: str) -> List[str]:
        """Unzips the ZIP file stream and returns a list of extracted file paths."""
        file_paths = []
        try:
            zip_file_stream.seek(0) # Ensure stream is at the beginning
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

    def _process_single_resume_for_bulk(self, file_path: str, user_id: int, organization_id: str, job_id: int, use_match_ai_client_v2: bool) -> Dict[str, Any]:
        """
        Helper method to process a single extracted resume file (from a bulk upload)
        and return its status and processed data. This is executed by worker threads.
        """
        file_name = os.path.basename(file_path)
        logger.debug(f"[Bulk Worker] Processing {file_name} (Path: {file_path})")
        try:
            # CRITICAL FIX: Call the correct methods on self.profile_management_service
            if use_match_ai_client_v2:
                processed_data = self.profile_management_service.process_uploaded_resume_v3( # Call V3 method
                    file_path=file_path,
                    user_id=user_id,
                    organization_id=organization_id,
                    file_name=file_name
                )
            else:
                with open(file_path, 'rb') as f:
                    file_stream = io.BytesIO(f.read())
                processed_data = self.profile_management_service.process_uploaded_resume_v1( # Call V1 method
                    file_stream=file_stream,
                    user_id=user_id,
                    organization_id=organization_id,
                    file_name=file_name
                )
            
            logger.info(f"[Bulk Worker] Successfully processed: {file_name} (DB ID: {processed_data.get('db_id', 'N/A')})")
            return {"status": "success", "file_name": file_name, "data": processed_data}
        except Exception as e:
            logger.error(f"[Bulk Worker] Error processing {file_name}: {e}", exc_info=True)
            return {"status": "error", "file_name": file_name, "error_message": str(e)}

    def _daemon_listener(self) -> None:
        """Daemon thread that listens to results and handles them (for logging/monitoring)."""
        logger.info("[Daemon] Starting result listener daemon thread.")
        while not self.stop_event.is_set() or not self.result_queue.empty():
            try:
                status, file_name, data = self.result_queue.get(timeout=1)
                logger.debug(f"[Daemon] Result: {status.upper()} - {file_name}")
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"[Daemon] Error in listener: {e}", exc_info=True)
        logger.info("[Daemon] Result listener daemon thread stopped.")

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

    def process_zip_file_for_resumes(self,
                                     zip_file_stream: io.BytesIO, # The incoming ZIP file stream
                                     user_id: int,
                                     organization_id: str,
                                     job_id: int,
                                     file_name: Optional[str] = "uploaded_zip.zip",
                                     use_match_ai_client_v2: bool = False,
                                     max_threads: Optional[int] = None) -> Dict[str, Any]:
        """
        Main entry point to process a zip file containing multiple resumes in parallel.
        It saves the ZIP to temp, unzips, processes files, and cleans up.
        """
        temp_zip_file_path = None
        temp_extract_dir = None
        all_processing_results = []
        
        try:
            # 1. Save the uploaded zip file stream to a temporary local file
            temp_zip_dir = tempfile.mkdtemp()
            temp_zip_file_path = os.path.join(temp_zip_dir, f"upload_{os.urandom(8).hex()}_{file_name}")
            
            zip_file_stream.seek(0) # Ensure stream is at the beginning
            with open(temp_zip_file_path, 'wb') as f:
                f.write(zip_file_stream.read())
            logger.info(f"Saved uploaded zip file to temporary local path: {temp_zip_file_path}")

            # 2. Unzip the file to another temporary local directory
            temp_extract_dir = tempfile.mkdtemp()
            extracted_file_paths = self._unzip_file_from_stream(zip_file_stream, temp_extract_dir) # Use the stream directly
            
            if not extracted_file_paths:
                raise ValueError("No valid files found in the ZIP archive.")

            # 3. Determine optimal thread count
            if max_threads is None:
                max_threads = self._get_optimal_thread_count()

            # 4. Start daemon listener thread
            self.stop_event.clear()
            daemon_thread = threading.Thread(target=self._daemon_listener, daemon=True)
            daemon_thread.start()
            logger.info("Starting thread pool for file processing.")

            # 5. Process files in parallel
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(self._process_single_resume_for_bulk, fp, user_id, organization_id, job_id, use_match_ai_client_v2) 
                    for fp in extracted_file_paths
                ]
                
                for future in as_completed(futures):
                    try:
                        result = future.result() 
                        all_processing_results.append(result)
                        self.result_queue.put(result) 
                    except Exception as e:
                        logger.error(f"Error getting result from future in bulk processing: {e}", exc_info=True)
                        all_processing_results.append({"status": "error", "file_name": "unknown_file_in_zip", "error_message": str(e)})

            # 6. Signal daemon to stop and wait for it
            self.stop_event.set()
            daemon_thread.join(timeout=5)
            if daemon_thread.is_alive():
                logger.warning("Daemon thread did not stop gracefully.")

            logger.info("Bulk processing complete.")
            return {"status": "completed", "total_files": len(extracted_file_paths), "results": all_processing_results}

        except Exception as e:
            logger.error(f"An error occurred during bulk file processing from storage: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "results": all_processing_results}
        finally:
            # Clean up temporary directories
            if temp_zip_file_path and os.path.exists(temp_zip_file_path):
                try:
                    os.remove(temp_zip_file_path)
                    logger.debug(f"Cleaned up zip file: {temp_zip_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove zip file {temp_zip_file_path}: {e}")
            
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                try:
                    shutil.rmtree(temp_extract_dir)
                    logger.debug(f"Cleaned up extracted files directory: {temp_extract_dir}")
                except Exception as e:
                    logger.warning(f"Failed to remove extracted files directory {temp_extract_dir}: {e}", exc_info=True)

    def process_zip_file_for_resumes_v2(self,
                                     zip_file_stream: io.BytesIO, # The incoming ZIP file stream
                                     user_id: int,
                                     organization_id: str,
                                     job_id: int,
                                     file_name: Optional[str] = "uploaded_zip.zip",
                                     use_match_ai_client_v2: bool = False,
                                     max_threads: Optional[int] = None) -> Dict[str, str]:
        """
        Asynchronously processes a zip file of resumes.

        This method performs the following steps:
        1. Saves the uploaded ZIP file to a persistent storage (e.g., AWS S3)
           using the FileStorageService.
        2. Creates a payload dictionary containing all necessary metadata for processing.
        3. Submits this payload to the FileTaskExecutorService to be processed in
           a background thread.
        4. Immediately returns a response indicating that the file is being processed.

        Args:
            zip_file_stream: The byte stream of the uploaded ZIP file.
            user_id: The ID of the user who uploaded the file.
            organization_id: The ID of the organization.
            job_id: The ID of the job associated with the resumes.
            file_name: The original name of the ZIP file.
            use_match_ai_client_v2: Flag to determine which parsing version to use.
            max_threads: The maximum number of threads for parallel processing.

        Returns:
            A dictionary confirming the task has been accepted for processing.
        """
        logger.info(f"V2: Received bulk upload '{file_name}' for org '{organization_id}' from user '{user_id}'.")

        try:
            # 1. Save the zip file to permanent storage (e.g., S3)
            storage_path, _ = self.file_storage_service.save_file(
                file_stream=zip_file_stream,
                original_filename=file_name
            )
            logger.info(f"V2: Saved '{file_name}' to permanent storage at: {storage_path}")

            # NEW: Create a record in the bulk_profile_uploads table
            upload_id = self.bulk_profile_upload_repository.create_upload_record(
                filename=file_name,
                user_id=user_id,
                organization_id=organization_id,
                job_id=job_id,
                status='processing',
                storage_path=storage_path
            )
            logger.info(f"V2: Created bulk upload tracking record with ID: {upload_id}")

            # 2. Create a dictionary object (payload) for the background task
            task_kwargs = {
                "zip_storage_path": storage_path,
                "user_id": user_id,
                "organization_id": organization_id,
                "job_id": job_id,
                "upload_id": upload_id,  # Pass the new ID to the background task
                "file_name": file_name,
                "use_match_ai_client_v2": use_match_ai_client_v2,
                "max_threads": max_threads,
            }

            # 3. Submit the task to the executor service to run in the background
            background_thread = threading.Thread(
                target=self.file_task_executor_service.execute_bulk_processing_task,
                kwargs=task_kwargs,
                daemon=True,
                name=f"BulkProcess-{file_name}"
            )
            background_thread.start()
            logger.info(f"V2: Dispatched bulk processing task for '{file_name}' to background executor.")

            # 4. Return an immediate response to the client
            return {"filename": file_name, "status": "processing"}

        except Exception as e:
            logger.error(f"V2: Failed to initiate bulk processing for '{file_name}': {e}", exc_info=True)
            # This is a synchronous failure before the async part even starts.
            raise RuntimeError(f"Failed to start bulk processing: {str(e)}")
        
    def get_bulk_upload_history(self, organization_id: str, job_id: int, user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
            """
            Retrieves the history of bulk uploads for a given organization, job, and user,
            with an optional date range.

            Args:
                organization_id: The organization to filter by.
                job_id: The job ID to filter by.
                user_id: The user ID to filter by.
                start_date: Optional start date for the filter range (YYYY-MM-DD).
                end_date: Optional end date for the filter range (YYYY-MM-DD).

            Returns:
                A list of dictionaries representing the bulk upload history.
            """
            logger.info(f"Fetching bulk upload history for org {organization_id}, job {job_id}, user {user_id}.")
            try:
                return self.bulk_profile_upload_repository.get_bulk_uploads(
                    organization_id=organization_id, job_id=job_id, user_id=user_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                logger.error(f"Service error getting bulk upload history for org {organization_id}, job {job_id}: {e}", exc_info=True)
                raise        