# database/job_description_repository.py

import logging
import json
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

from models.job_description_models import JobDescription 

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) 

class JobDescriptionRepository:
    def __init__(self):
        logger.info("JobDescriptionRepository initialized.")

    def save_job_description(self, jd_data: JobDescription, embedding: List[float], user_id: int, organization_id: str, jd_organization_type: Optional[str] = None, parent_org_id: Optional[str] = None) -> int:
        """
        Saves a parsed Job Description (JobDescription Pydantic object) and its embedding into the database,
        along with user_id, organization_id, user_tags, and is_active status.
        Returns the ID of the inserted JD.
        """
        session = get_db_session()
        try:
            jd_dict = jd_data.model_dump(by_alias=True) 
            jd_json_str = json.dumps(jd_dict) # This is correct for saving JSONB
            
            embedding_str = f"[{','.join(map(str, embedding))}]" if embedding else None

            if user_id is None or organization_id is None:
                logger.error("Attempted to save JD without user_id or organization_id.")
                raise ValueError("User ID and Organization ID are required to save a JD.")

            user_tags = jd_data.user_tags if jd_data.user_tags else []
            is_active = jd_data.is_active
            jd_version = jd_data.jd_version # NEW: Get version from Pydantic object

            query = text("""
                INSERT INTO job_descriptions (job_details, embedding, user_id, organization_id, user_tags, is_active, jd_version, jd_organization_type, parent_org_id)
                VALUES (:jd_json, :embedding_vector, :user_id, :organization_id, :user_tags, :is_active, :jd_version, :jd_organization_type, :parent_org_id)
                RETURNING id;
            """)

            result = session.execute(query, {
                'jd_json': jd_json_str,
                'embedding_vector': embedding_str,
                'user_id': user_id,
                'organization_id': organization_id,
                'user_tags': json.dumps(user_tags), # Store as JSONB string
                'is_active': is_active,             # Store as boolean
                'jd_version': jd_version,           # NEW: Store version
                'jd_organization_type': jd_organization_type, # NEW: Store organization type
                'parent_org_id': parent_org_id # NEW: Store parent org id
            })            

            jd_id = result.scalar_one()
            session.commit()
            logger.info(f"Job Description '{jd_data.job_title}' (Version: {jd_version}) saved with ID: {jd_id} for user {user_id} in org {organization_id}.")
            return jd_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving Job Description to database: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_job_descriptions_by_organization(self, organization_id: str, include_inactive: bool = False, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all job descriptions associated with a specific organization.
        Optionally includes inactive JDs and supports tag-based filtering.
        """
        session = get_db_session()
        try:
            where_clauses = ["organization_id = :organization_id"]
            params = {'organization_id': organization_id}

            if filters:
                if 'user_tag' in filters and filters['user_tag']:
                    where_clauses.append("user_tags @> :user_tag_filter")
                    params['user_tag_filter'] = json.dumps([filters['user_tag']])
                if 'jd_version' in filters and filters['jd_version'] is not None: # NEW: Filter by jd_version
                    where_clauses.append("jd_version = :jd_version")
                    params['jd_version'] = filters['jd_version']

            sql_query = """
                SELECT id, job_details, embedding, organization_id, user_id, user_tags, is_active, jd_version, created_at, updated_at -- NEW: Select jd_version
                FROM job_descriptions
                WHERE """ + " AND ".join(where_clauses) + """
                ORDER BY created_at DESC;
            """
            
            results = session.execute(text(sql_query), params).fetchall()
            
            jds = []
            for row in results:
                jd_dict = row.job_details 
                
                jd_dict['id'] = row.id 
                jd_dict['organizationId'] = row.organization_id 
                jd_dict['userId'] = row.user_id 
                jd_dict['userTags'] = row.user_tags 
                jd_dict['isActive'] = row.is_active 
                jd_dict['jdVersion'] = row.jd_version # NEW: Include jd_version
                jd_dict['createdAt'] = row.created_at.isoformat()
                jd_dict['updatedAt'] = row.updated_at.isoformat()
                
                jds.append(jd_dict)
            logger.info(f"Retrieved {len(jds)} JDs for organization '{organization_id}'.")
            return jds
        except Exception as e:
            session.rollback() # Rollback in case of an error during retrieval to release connection
            logger.error(f"Error retrieving JDs for organization '{organization_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()


    def semantic_search_job_descriptionsv1(
        self,
        query_embedding: List[float],
        organization_id: str,
        limit: int = 10,
        min_similarity: float = 0.1,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic search on stored Job Descriptions using pgvector embedding comparison.
        Returns matching results sorted by similarity.
        """
        session = get_db_session()
        try:
            if len(query_embedding) != 768:
                raise ValueError("Expected 768-dimensional embedding")

            # Convert list to pgvector-compatible string: [0.1,0.2,...]
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            params = {
                'organization_id': organization_id,
                'limit': limit,
                'query_embedding': query_embedding_str
            }

            # Build WHERE clause
            where_clauses = ["embedding IS NOT NULL", "organization_id = :organization_id"]

            if filters:
                if 'is_active' in filters and filters['is_active'] is not None:
                    where_clauses.append("is_active = :is_active")
                    params['is_active'] = filters['is_active']

                if 'user_tag' in filters and filters['user_tag']:
                    where_clauses.append("user_tags @> :user_tag_filter")
                    params['user_tag_filter'] = [filters['user_tag']]  # Pass as list, not JSON string

            sql_query = f"""
                SELECT id,
                    job_details->>'job_title' AS job_title,
                    job_details->>'location' AS location,
                    organization_id AS orgid,
                    user_id AS userid,
                    user_tags,
                    is_active,
                    (embedding <=> CAST(:query_embedding AS vector)) AS cosine_distance
                FROM job_descriptions
                WHERE {" AND ".join(where_clauses)}
                ORDER BY cosine_distance ASC
                LIMIT :limit;
            """

            logger.debug(f"Query: {sql_query} | Params: {params}")
            results = session.execute(text(sql_query), params).fetchall()

            search_results = []
            for row in results:
                similarity = 1 - row.cosine_distance
                if similarity >= min_similarity:
                    search_results.append({
                        "id": row.id,
                        "jobTitle": row.job_title,
                        "location": row.location,
                        "organizationId": row.orgid,
                        "userId": row.userid,
                        "userTags": row.user_tags,
                        "isActive": row.is_active,
                        "similarityScore": round(similarity, 4)
                    })

            logger.info(f"Semantic search for org '{organization_id}' found {len(search_results)} results.")
            return search_results

        except Exception as e:
            session.rollback()
            logger.error(f"Error in semantic search for org {organization_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def semantic_search_job_descriptions(self, query_embedding: List[float], organization_id: str, limit: int = 10, min_similarity: float = 0.1, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic search on stored Job Descriptions based on a query embedding, filtered by organization_id.
        Returns a list of JD IDs, titles, orgId, and user_id sorted by similarity.
        Supports filtering by tags, active status, and jd_version.
        """
        session = get_db_session()
        try:
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            where_clauses = ["embedding IS NOT NULL", "organization_id = :organization_id"]
            params = {'organization_id': organization_id, 'limit': limit, 'min_similarity_val': min_similarity} 

            max_cosine_distance = 1 - min_similarity 
            where_clauses.append(f"(embedding <=> '{query_embedding_str}') <= :max_cosine_distance") 
            params['max_cosine_distance'] = max_cosine_distance 

            # Filter by is_active
            if filters and 'is_active' in filters and filters['is_active'] is not None:
                where_clauses.append("is_active = :is_active")
                params['is_active'] = filters['is_active']

            # Filter by user_tags in semantic search
            if filters and 'user_tag' in filters and filters['user_tag']:
                where_clauses.append("user_tags @> :user_tag_filter")
                params['user_tag_filter'] = json.dumps([filters['user_tag']])
            
            # NEW: Filter by jd_version in semantic search
            if filters and 'jd_version' in filters and filters['jd_version'] is not None:
                where_clauses.append("jd_version = :jd_version")
                params['jd_version'] = filters['jd_version']


            sql_query = f"""
                SELECT id, job_details->>'job_title' AS job_title, job_details->>'location' AS location,
                       organization_id AS orgid, user_id AS userid, user_tags, is_active, jd_version, -- NEW: Select jd_version
                       (embedding <=> '{query_embedding_str}') AS cosine_distance
                FROM job_descriptions
                WHERE """ + " AND ".join(where_clauses) + """
                ORDER BY cosine_distance ASC
                LIMIT :limit;
            """
            
            results = session.execute(text(sql_query), params).fetchall()
            
            search_results = []
            for row in results:
                similarity = 1 - row.cosine_distance
                search_results.append({
                    "id": row.id,
                    "jobTitle": row.job_title, 
                    "location": row.location,
                    "organizationId": row.orgid, 
                    "userId": row.userid,       
                    "userTags": row.user_tags, 
                    "isActive": row.is_active, 
                    "jdVersion": row.jd_version, # NEW: Include jd_version
                    "similarityScore": round(similarity, 4)
                })
            
            search_results.sort(key=lambda x: x['similarityScore'], reverse=True)
            
            logger.info(f"Performed semantic search on JDs for org {organization_id}. Found {len(search_results)} results with filters {filters} and min_similarity {min_similarity}.")
            return search_results
        except Exception as e:
            session.rollback()
            logger.error(f"Error during semantic search on JDs for org {organization_id} with filters {filters}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def semantic_search_job_descriptions_gemini(self, query_embedding: List[float], organization_id: str, limit: int = 10, min_similarity: float = 0.1, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic search on stored Job Descriptions based on a query embedding, filtered by organization_id.
        Returns a list of JD IDs, titles, orgId, and user_id sorted by similarity.
        Supports filtering by tags and active status.
        """
        session = get_db_session()
        try:
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            where_clauses = ["embedding IS NOT NULL", "organization_id = :organization_id"]
            params = {'organization_id': organization_id, 'limit': limit}

            if filters and 'is_active' in filters and filters['is_active'] is not None:
                where_clauses.append("is_active = :is_active")
                params['is_active'] = filters['is_active']

            if filters and 'user_tag' in filters and filters['user_tag']:
                where_clauses.append("user_tags @> :user_tag_filter")
                params['user_tag_filter'] = json.dumps([filters['user_tag']])


            sql_query = f"""
                SELECT id, job_details->>'job_title' AS job_title, job_details->>'location' AS location,
                       organization_id AS orgid, user_id AS userid, user_tags, is_active,
                       (embedding <=> '{query_embedding_str}') AS cosine_distance
                FROM job_descriptions
                WHERE """ + " AND ".join(where_clauses) + """
                ORDER BY cosine_distance ASC
                LIMIT :limit;
            """
            logger.debug(f"Query - {sql_query}");
            results = session.execute(text(sql_query), params).fetchall()
            
            search_results = []
            for row in results:
                similarity = 1 - row.cosine_distance
                if similarity >= min_similarity:
                    search_results.append({
                        "id": row.id,
                        "jobTitle": row.job_title, 
                        "location": row.location,
                        "organizationId": row.orgid, 
                        "userId": row.userid,       
                        "userTags": row.user_tags, # CRITICAL FIX: Access directly, no json.loads()
                        "isActive": row.is_active, 
                        "similarityScore": round(similarity, 4)
                    })
            
            search_results.sort(key=lambda x: x['similarityScore'], reverse=True)
            
            logger.info(f"Performed semantic search on JDs for org {organization_id}. Found {len(search_results)} results with filters {filters}.")
            return search_results
        except Exception as e:
            session.rollback() # Rollback in case of an error during retrieval
            logger.error(f"Error during semantic search on JDs for org {organization_id} with filters {filters}: {e}", exc_info=True)
            raise
        finally:
            session.close()
            
    def get_job_description_by_id(self, jd_id: int, organization_id: str) -> Optional[Dict[str, Any]]: # NEW METHOD
        """
        Retrieves a single Job Description by its ID, filtered by organization_id.
        """
        session = get_db_session()
        try:
            query = text("""
                SELECT id, job_details, embedding, organization_id, user_id, user_tags, is_active, jd_version, created_at, updated_at
                FROM job_descriptions
                WHERE id = :jd_id AND organization_id = :organization_id AND is_active = TRUE;
            """)
            
            result = session.execute(query, {'jd_id': jd_id, 'organization_id': organization_id}).fetchone()
            
            if result:
                jd_dict = result.job_details # Already a dict from JSONB
                jd_dict['id'] = result.id 
                jd_dict['organizationId'] = result.organization_id 
                jd_dict['userId'] = result.user_id 
                jd_dict['userTags'] = result.user_tags 
                jd_dict['isActive'] = result.is_active 
                jd_dict['jdVersion'] = result.jd_version
                jd_dict['createdAt'] = result.created_at.isoformat()
                jd_dict['updatedAt'] = result.updated_at.isoformat()
                # Embedding is a large vector, only include if explicitly needed, usually not for detail view
                # jd_dict['embedding'] = result.embedding 
                return jd_dict
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"Error retrieving JD by ID {jd_id} for organization '{organization_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()

    def count_active_job_descriptions(self, organization_id: str, by_parent_org: bool = False) -> int:
        """
        Counts the number of active job descriptions for a given organization.

        Args:
            organization_id (str): The ID of the organization.
            by_parent_org (bool): If True, counts by parent_org_id instead of organization_id.

        Returns:
            int: The count of active job descriptions.
        """
        session = get_db_session()
        try:
            column_to_filter = "parent_org_id" if by_parent_org else "organization_id"
            
            query = text(f"""
                SELECT COUNT(*)
                FROM job_descriptions
                WHERE {column_to_filter} = :organization_id AND is_active = TRUE;
            """)
            
            result = session.execute(query, {'organization_id': organization_id}).scalar_one_or_none()
            
            count = result if result is not None else 0
            logger.info(f"Found {count} active JDs for org '{organization_id}' (by_parent_org={by_parent_org}).")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error counting active JDs for organization '{organization_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()
    