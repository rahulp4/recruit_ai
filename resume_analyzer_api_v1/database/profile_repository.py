# database/profile_repository.py
import logging
import json
from sqlalchemy import text
from database.postgres_manager import get_db_session
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class ProfileRepository:
    """
    Data Access Layer for Profile entities.
    Handles all direct interaction with the 'profiles' table in PostgreSQL.
    """
    def __init__(self):
        logger.info("ProfileRepository initialized.")


    def get_profile_by_id(self, profile_id: int, organization_id: str) -> Optional[Dict[str, Any]]: 
        """
        Retrieves a single candidate profile by its ID, filtered by organization_id.
        Returns the full profile_data JSONB content as a dictionary.
        """
        session = get_db_session()
        try:
            # CRITICAL FIX: Removed updated_at from SELECT query
            logger.info("ProfileRepository initialized.")
            query = text("""
                SELECT id, profile_data, embedding, user_id, organization_id, created_at
                FROM profiles
                WHERE id = :profile_id AND organization_id = :organization_id;
            """)
            
            result = session.execute(query, {'profile_id': profile_id, 'organization_id': organization_id}).fetchone()
            
            if result:
                profile_dict_from_db = result.profile_data 
                profile_dict_from_db['id'] = result.id 
                profile_dict_from_db['organizationId'] = result.organization_id 
                profile_dict_from_db['userId'] = result.user_id 
                profile_dict_from_db['createdAt'] = result.created_at.isoformat()
                # CRITICAL FIX: Removed access to row.updated_at
                # profile_dict_from_db['updatedAt'] = result.updated_at.isoformat() 
                return profile_dict_from_db
            return None
        except Exception as e:
            session.rollback() 
            logger.error(f"Error retrieving profile by ID {profile_id} for organization '{organization_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()
            
    def save_profile(self, profile_data: dict, embedding: list, user_id: int, organization_id: str, filebatchid: Optional[str] = None, jd_organization_type: Optional[str] = None, parent_org_id: Optional[str] = None):
        """
        Saves a parsed profile (JSONB) and its embedding into the database,
        along with user_id, organization_id, and an optional filebatchid in dedicated columns.
        Returns the ID of the inserted profile.
        Also saves the organization type and parent organization ID.
        """
        session = get_db_session()
        try:
            # Convert Python dict to JSON string for JSONB column
            profile_json_str = json.dumps(profile_data)
            
            # Convert Python list of floats to PostgreSQL vector string format
            embedding_str = f"[{','.join(map(str, embedding))}]" if embedding else None

            if user_id is None or organization_id is None:
                logger.error("Attempted to save profile without user_id or organization_id.")
                raise ValueError("User ID and Organization ID are required to save a profile.")

            query = text("""
                INSERT INTO profiles (profile_data, embedding, user_id, organization_id, filebatchid, jd_organization_type, parent_org_id)
                VALUES (:profile_json, :embedding_vector, :user_id, :organization_id, :filebatchid, :jd_organization_type, :parent_org_id)
                RETURNING id;
            """)
            
            result = session.execute(query, {
                'profile_json': profile_json_str,
                'embedding_vector': embedding_str,
                'user_id': user_id,
                'organization_id': organization_id,
                'filebatchid': filebatchid,
                'jd_organization_type': jd_organization_type,
                'parent_org_id': parent_org_id
            })
            
            profile_id = result.scalar_one() 
            session.commit()
            logger.info(f"Profile for {profile_data.get('name', 'Unknown')} saved with ID: {profile_id} for user {user_id} in org {organization_id}")
            return profile_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving profile to database: {e}", exc_info=True)
            raise
        finally:
            session.close()

    # find_all_profiles method (if needed for admin, otherwise not used by profile_routes)
    def find_all_profiles(self, organization_id=None):
        """Retrieves all profiles from the database, optionally filtered by organization_id."""
        session = get_db_session()
        try:
            query_str = "SELECT id, profile_data FROM profiles"
            params = {}
            if organization_id:
                query_str += " WHERE organization_id = :organization_id"
                params['organization_id'] = organization_id
            
            query = text(query_str + ";") # Added semicolon for safety
            results = session.execute(query, params).fetchall()
            
            profiles = []
            for row in results:
                profile_dict = json.loads(row.profile_data)
                profile_dict['id'] = row.id
                profiles.append(profile_dict)
            logger.info(f"Found {len(profiles)} profiles for organization_id: {organization_id if organization_id else 'ALL'}")
            return profiles
        except Exception as e:
            logger.error(f"Error finding profiles for organization {organization_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    # semantic_search_profiles method
    def semantic_search_profiles(self, query_embedding, organization_id, limit=10, min_similarity=0.1):
        """
        Performs semantic search using vector similarity, filtered by organization_id.
        Returns a list of profile names and similarity scores.
        """
        session = get_db_session()
        try:
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            query = text(f"""
                SELECT id, profile_data->>'name' AS name, 
                       (embedding <=> '{query_embedding_str}') AS cosine_distance
                FROM profiles
                WHERE embedding IS NOT NULL AND organization_id = :organization_id
                ORDER BY cosine_distance ASC
                LIMIT :limit;
            """)
            
            results = session.execute(query, {'organization_id': organization_id, 'limit': limit}).fetchall()
            
            search_results = []
            for row in results:
                similarity = 1 - row.cosine_distance
                if similarity >= min_similarity:
                    search_results.append({
                        "id": row.id,
                        "name": row.name,
                        "similarity_score": similarity
                    })
            
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Performed semantic search for org {organization_id}. Found {len(search_results)} results.")
            return search_results
        except Exception as e:
            logger.error(f"Error during semantic search for org {organization_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    # filter_profiles_by_criteria method
    def filter_profiles_by_criteria(self, filters, organization_id, limit=100):
        """
        Filters profiles based on structured criteria, filtered by organization_id.
        Filters is a dict like {'name': 'Rahul', 'min_total_yoe': 5, 'skill': 'Python'}
        """
        session = get_db_session()
        try:
            where_clauses = ["organization_id = :organization_id"] # Always filter by organization
            params = {'organization_id': organization_id}

            if 'name' in filters:
                where_clauses.append("profile_data->>'name' ILIKE :name_filter")
                params['name_filter'] = f"%{filters['name']}%"
            
            if 'min_total_yoe' in filters:
                where_clauses.append("CAST(profile_data->>'total_experience_years' AS NUMERIC) >= :min_total_yoe")
                params['min_total_yoe'] = filters['min_total_yoe']
                
            if 'qualification' in filters:
                where_clauses.append("profile_data->'education' @> :qualification_filter")
                params['qualification_filter'] = json.dumps([{"degree": filters['qualification']}]) # JSONB containment needs valid JSON
            
            if 'skill' in filters:
                # This type of OR query on JSONB fields can be tricky for performance without specific expression indexes.
                # The GIN index on profile_data helps, but specific expression indexes on skills arrays would be better.
                skill_to_check = filters['skill']
                skill_clauses = []
                for skill_cat in ['languages', 'frameworks', 'databases', 'tools', 'platforms', 'methodologies', 'other']:
                    # Check if the skill is present in the array for this category
                    # Using JSONB array containment operator <@ or the existence operator ?
                    # `profile_data->'skills'->'languages' @> '["Python"]'` (exact match in array)
                    # `profile_data->'skills'->'languages' ? 'Python'` (key 'Python' exists as element)
                    skill_clauses.append(f"profile_data->'skills'->'{skill_cat}' @> :skill_array_filter")
                where_clauses.append(f"({ ' OR '.join(skill_clauses) })")
                params['skill_array_filter'] = json.dumps([skill_to_check]) # Check if array contains this skill


            if 'tech_experience' in filters and isinstance(filters['tech_experience'], dict):
                tech_name = filters['tech_experience'].get('name')
                min_years = filters['tech_experience'].get('min_years')
                if tech_name and min_years is not None:
                    # Ensure tech_name is properly escaped if used directly in f-string key, but here it's fine as it's a key.
                    where_clauses.append(f"CAST(profile_data->'technology_experience_years'->>'{tech_name.lower().strip()}' AS NUMERIC) >= :min_tech_years")
                    params['min_tech_years'] = min_years


            sql_query = "SELECT id, profile_data->>'name' AS name FROM profiles"
            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)
            sql_query += " LIMIT :limit;"
            
            logger.debug(f"Executing filter query: {sql_query} with params: {params}")
            results = session.execute(text(sql_query), {**params, 'limit': limit}).fetchall()
            
            filtered_profiles = [{"id": row.id, "name": row.name} for row in results]
            logger.info(f"Filtered profiles for org {organization_id}. Found {len(filtered_profiles)} results.")
            return filtered_profiles
        except Exception as e:
            logger.error(f"Error during profile filtering for org {organization_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def count_profiles_for_organization(self, organization_id: str, by_parent_org: bool = False) -> int:
        """
        Counts the number of profiles for a given organization.

        Args:
            organization_id (str): The ID of the organization.
            by_parent_org (bool): If True, counts by parent_org_id instead of organization_id.

        Returns:
            int: The count of profiles.
        """
        session = get_db_session()
        try:
            column_to_filter = "parent_org_id" if by_parent_org else "organization_id"
            
            query = text(f"""
                SELECT COUNT(*)
                FROM profiles
                WHERE {column_to_filter} = :organization_id;
            """)
            
            result = session.execute(query, {'organization_id': organization_id}).scalar_one_or_none()
            
            count = result if result is not None else 0
            logger.info(f"Found {count} profiles for org '{organization_id}' (by_parent_org={by_parent_org}).")
            return count
        except Exception as e:
            session.rollback()
            logger.error(f"Error counting profiles for organization '{organization_id}': {e}", exc_info=True)
            raise
        finally:
            session.close()