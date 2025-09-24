# database/bulk_profile_upload_repository.py
import logging
import uuid
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class BulkProfileUploadRepository:
    """
    Data Access Layer for bulk profile upload tracking.
    Handles all direct interaction with the 'bulk_profile_uploads' table.
    """
    def __init__(self):
        logger.info("BulkProfileUploadRepository initialized.")

    def create_upload_record(self, filename: str, user_id: int, organization_id: str, job_id: int, status: str, storage_path: str) -> str:
        """
        Creates a new record for a bulk upload and returns its UUID.

        Args:
            filename: The original name of the uploaded ZIP file.
            user_id: The ID of the user who initiated the upload.
            organization_id: The organization the upload belongs to.
            job_id: The job the upload is associated with.
            status: The initial status (e.g., 'processing').
            storage_path: The path where the ZIP file is stored (e.g., S3 URI).

        Returns:
            The UUID of the newly created record as a string.
        """
        session = get_db_session()
        upload_id = str(uuid.uuid4())
        try:
            query = text("""
                INSERT INTO bulk_profile_uploads (id, filename, user_id, organization_id, job_id, status, storage_path)
                VALUES (:id, :filename, :user_id, :organization_id, :job_id, :status, :storage_path)
                RETURNING id;
            """)
            
            inserted_id = session.execute(query, {
                'id': upload_id,
                'filename': filename,
                'user_id': user_id,
                'organization_id': organization_id,
                'job_id': job_id,
                'status': status,
                'storage_path': storage_path
            }).scalar_one()
            
            session.commit()
            logger.info(f"Created bulk upload record with ID: {inserted_id} for file '{filename}'")
            return inserted_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating bulk upload record: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_bulk_uploads(self, organization_id: str, job_id: int, user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of bulk uploads based on specified filters.

        Args:
            organization_id: The organization to filter by.
            job_id: The job ID to filter by.
            user_id: The user ID to filter by.
            start_date: Optional start date for the filter range (YYYY-MM-DD).
            end_date: Optional end date for the filter range (YYYY-MM-DD).

        Returns:
            A list of dictionaries, each representing a bulk upload record.
        """
        session = get_db_session()
        try:
            params = {'organization_id': organization_id, 'job_id': job_id, 'user_id': user_id}
            
            query_str = """
                SELECT id, filename, status, created_at, updated_at
                FROM bulk_profile_uploads
                WHERE organization_id = :organization_id
                  AND job_id = :job_id
                  AND user_id = :user_id
            """
            
            if start_date:
                query_str += " AND created_at >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                query_str += " AND created_at < CAST(:end_date AS DATE) + INTERVAL '1 day'"
                params['end_date'] = end_date
                
            query_str += " ORDER BY created_at DESC;"
            
            results = session.execute(text(query_str), params).fetchall()
            
            return [{
                "upload_id": str(row.id), "filename": row.filename, "status": row.status,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            } for row in results]
        except Exception as e:
            logger.error(f"Error getting bulk uploads for org {organization_id}, job {job_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def update_upload_status(self, upload_id: str, status: str):
        """
        Updates the status of a bulk upload record.
        """
        session = get_db_session()
        try:
            query = text("UPDATE bulk_profile_uploads SET status = :status, updated_at = NOW() WHERE id = :upload_id;")
            session.execute(query, {'upload_id': upload_id, 'status': status})
            session.commit()
            logger.info(f"Updated bulk upload record {upload_id} to status '{status}'")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating bulk upload record {upload_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()