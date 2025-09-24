import logging
import json
from sqlalchemy import text
from database.postgres_manager import get_db_session

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ProfileRepositoryRemove:
    """
    Data Access Layer for Profile entities.
    Handles all direct interaction with the 'profiles' table in PostgreSQL.
    """
    def __init__(self):
        logger.info("ProfileRepository initialized.")

    def save_profile(self, profile_data, embedding):
        """
        Saves a parsed profile (JSONB) and its embedding into the database.
        Returns the ID of the inserted profile.
        """
        session = get_db_session()
        try:
            # Convert Python dict to JSON string for JSONB column
            profile_json_str = json.dumps(profile_data)
            
            # Convert Python list of floats to PostgreSQL vector string format
            # pgvector expects '[]' format for vector type
            embedding_str = f"[{','.join(map(str, embedding))}]" if embedding else None

            query = text("""
                INSERT INTO profiles (profile_data, embedding)
                VALUES (:profile_json, :embedding_vector)
                RETURNING id;
            """)
            
            result = session.execute(query, {
                'profile_json': profile_json_str,
                'embedding_vector': embedding_str
            })
            
            profile_id = result.scalar_one() # Get the ID of the newly inserted row
            session.commit()
            logger.info(f"Profile for {profile_data.get('name', 'Unknown')} saved with ID: {profile_id}")
            return profile_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving profile to database: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def find_all_profiles(self):
        """Retrieves all profiles from the database."""
        session = get_db_session()
        try:
            query = text("SELECT id, profile_data FROM profiles;")
            results = session.execute(query).fetchall()
            
            profiles = []
            for row in results:
                profile_dict = json.loads(row.profile_data) # Convert JSONB back to Python dict
                profile_dict['id'] = row.id # Add the database ID
                profiles.append(profile_dict)
            return profiles
        except Exception as e:
            logger.error(f"Error finding all profiles: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def semantic_search_profiles(self, query_embedding, limit=10, min_similarity=0.1):
        """
        Performs semantic search using vector similarity.
        Returns a list of profile names and similarity scores.
        """
        session = get_db_session()
        try:
            # pgvector uses '<=>' for L2 distance (Euclidean) or '<->' for cosine distance (1 - cosine_similarity)
            # For cosine similarity, we use vector_cosine_ops in the index and calculate 1 - (embedding <=> query_embedding)
            # Or, if you want direct similarity, you can use dot product and normalize.
            # Let's use cosine distance for direct pgvector operator.
            # The operator '<->' computes cosine distance. Lower is more similar.
            # So, we'll order by ASC and filter by a maximum distance.
            
            # Convert query embedding to pgvector string format
            query_embedding_str = f"[{','.join(map(str, query_embedding))}]"

            # Note: For cosine similarity, pgvector's '<=>' operator (used with vector_cosine_ops index)
            # calculates cosine distance (1 - cosine_similarity). So, smaller values are more similar.
            # We'll use this and convert to similarity score (1 - distance) for output.
            query = text(f"""
                SELECT id, profile_data->>'name' AS name, 
                       (embedding <=> '{query_embedding_str}') AS cosine_distance
                FROM profiles
                WHERE embedding IS NOT NULL
                ORDER BY cosine_distance ASC
                LIMIT :limit;
            """)
            
            results = session.execute(query, {'limit': limit}).fetchall()
            
            search_results = []
            for row in results:
                # Cosine similarity = 1 - Cosine Distance
                similarity = 1 - row.cosine_distance
                if similarity >= min_similarity:
                    search_results.append({
                        "id": row.id,
                        "name": row.name,
                        "similarity_score": similarity
                    })
            
            # Sort by similarity score in descending order (highest similarity first)
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Performed semantic search. Found {len(search_results)} results.")
            return search_results
        except Exception as e:
            logger.error(f"Error during semantic search: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def filter_profiles_by_criteria(self, filters, limit=100):
        """
        Filters profiles based on structured criteria.
        Filters is a dict like {'name': 'Rahul', 'min_yoe': 5, 'skills.languages': 'Python'}
        """
        session = get_db_session()
        try:
            where_clauses = []
            params = {}

            # Example filters (extend as needed based on your JSON structure)
            if 'name' in filters:
                where_clauses.append("profile_data->>'name' ILIKE :name_filter")
                params['name_filter'] = f"%{filters['name']}%"
            
            if 'min_yoe' in filters:
                # This assumes you have a 'total_experience_years' field or similar
                # within your profile_data JSONB. We'll use a simplified check here.
                # For more complex YOE, you'd calculate it from experience dates.
                where_clauses.append("CAST(profile_data->>'summary' AS TEXT) ~ :yoe_regex")
                # This is a very rough regex for "X years experience".
                # A better approach is to parse YOE into a dedicated field during LLM parsing.
                params['yoe_regex'] = f"\\b[0-9]+\\s+years?\\b|\\b{filters['min_yoe']}\\+\\s*years?\\b"
                # A more robust YOE filter would be:
                # where_clauses.append("CAST(profile_data->'total_experience_years' AS NUMERIC) >= :min_yoe")
                # params['min_yoe'] = filters['min_yoe']

            if 'qualification' in filters:
                where_clauses.append("profile_data->'education' @> :qualification_filter")
                params['qualification_filter'] = json.dumps([{"degree": filters['qualification']}])
            
            if 'skill' in filters:
                # Search within any skill category
                where_clauses.append("""
                    profile_data->'skills'->'languages' ? :skill_filter OR
                    profile_data->'skills'->'frameworks' ? :skill_filter OR
                    profile_data->'skills'->'databases' ? :skill_filter OR
                    profile_data->'skills'->'tools' ? :skill_filter OR
                    profile_data->'skills'->'platforms' ? :skill_filter OR
                    profile_data->'skills'->'methodologies' ? :skill_filter OR
                    profile_data->'skills'->'other' ? :skill_filter
                """)
                params['skill_filter'] = filters['skill'] # Case-sensitive by default, use ILIKE for text

            # For "worked on Spring Boot for 5 years" - this combines structured and calculated data
            if 'tech_experience' in filters and isinstance(filters['tech_experience'], dict):
                tech_name = filters['tech_experience'].get('name')
                min_years = filters['tech_experience'].get('min_years')
                if tech_name and min_years is not None:
                    # Access the calculated 'technology_experience_years'
                    where_clauses.append(f"CAST(profile_data->'technology_experience_years'->>'{tech_name.lower()}' AS NUMERIC) >= :min_tech_years")
                    params['min_tech_years'] = min_years


            sql_query = "SELECT id, profile_data->>'name' AS name FROM profiles"
            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)
            sql_query += " LIMIT :limit;"
            
            results = session.execute(text(sql_query), {**params, 'limit': limit}).fetchall()
            
            filtered_profiles = [{"id": row.id, "name": row.name} for row in results]
            logger.info(f"Filtered profiles. Found {len(filtered_profiles)} results.")
            return filtered_profiles
        except Exception as e:
            logger.error(f"Error during profile filtering: {e}", exc_info=True)
            raise
        finally:
            session.close()