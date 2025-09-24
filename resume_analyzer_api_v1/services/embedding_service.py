import logging
import google.generativeai as genai
import numpy as np
import os

logger = logging.getLogger(__name__)
# Let app.py's root logger control the level, or set explicitly:
# logger.setLevel(logging.DEBUG) 

class EmbeddingService:
    """
    Handles generating text embeddings and calculating cosine similarity.
    """
    def __init__(self, api_key):
        if not api_key:
            logger.error("Gemini API Key not provided to EmbeddingService.")
            raise ValueError("Gemini API Key is required.")
        genai.configure(api_key=api_key)
        logger.info("EmbeddingService initialized.")

    def generate_embedding(self, text):
        """Generates an embedding vector for the given text using the Gemini embedding model."""
        if not text or not text.strip():
            logger.warning("Attempted to generate embedding for empty or whitespace text.")
            return None
        try:
            # Corrected: Use 'models/' prefix for the embedding model name
            result = genai.embed_content(model='models/embedding-001', content=text)
            
            if result and result.get('embedding'): # Check if 'embedding' key exists and has a value
                return result['embedding']
            logger.warning(f"Embedding generation returned no embedding for text: '{text[:50]}...' Response: {result}")
            return None
        except Exception as e:
            logger.error(f"Error generating embedding for text: '{text[:50]}...'. Error: {e}", exc_info=True)
            return None

    @staticmethod
    def cosine_similarity(vec1, vec2):
        """Calculates cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        dot_product = np.dot(vec1_np, vec2_np)
        norm_a = np.linalg.norm(vec1_np)
        norm_b = np.linalg.norm(vec2_np)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def build_text_for_embedding(self, parsed_data):
        """Concatenates relevant text fields from parsed data for embedding."""
        text_builder = []
        if parsed_data.get('name'):
            text_builder.append(parsed_data['name'])
        if parsed_data.get('summary'):
            text_builder.append(parsed_data['summary'])

        # UPDATED SKILLS PROCESSING
        if parsed_data.get('skills'):
            skills_section = parsed_data['skills']
            if isinstance(skills_section, dict): # Ensure it's a dictionary
                for category_name, skills_list in skills_section.items():
                    if isinstance(skills_list, list):
                        for skill_item in skills_list:
                            if isinstance(skill_item, dict): # New structure: list of objects
                                skill_name = skill_item.get('name')
                                experience_years = skill_item.get('experience_years')
                                if skill_name:
                                    skill_text = skill_name
                                    if experience_years is not None:
                                        skill_text += f" ({experience_years} years)"
                                    text_builder.append(skill_text)
                            elif isinstance(skill_item, str): # Fallback if LLM returns simple string
                                text_builder.append(skill_item)
            elif isinstance(skills_section, list): # Old fallback structure (should ideally not happen with new prompt)
                 logger.warning("Skills data is a list, expecting a dictionary of categories. Processing as flat list.")
                 for skill_item in skills_section:
                     if isinstance(skill_item, str):
                         text_builder.append(skill_item)


        if parsed_data.get('experience'):
            for exp in parsed_data['experience']:
                if exp.get('description'):
                    text_builder.append(exp['description'])
        if parsed_data.get('projects'):
            for proj in parsed_data['projects']:
                if proj.get('description'):
                    text_builder.append(proj['description'])
        
        return " ".join(text_builder).strip()