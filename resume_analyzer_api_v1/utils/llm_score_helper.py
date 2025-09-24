import google.generativeai as genai
import json
from typing import Dict, Any, Optional, List, Union, Tuple

def compute_gemini_vector_score(model: genai.GenerativeModel, req_data: str, candidate_data: Union[str, List[str]]) -> Tuple[float, float]:
    """
    Computes a vector-like score by asking Gemini to compare two strings and return a similarity score.
    """
    print(f" req_data ",req_data)
    print(f" candidate_data ",candidate_data)
    candidate_text = ""
    if isinstance(candidate_data, list):
        candidate_text = "\n".join(candidate_data)
    else:
        candidate_text = candidate_data
    
    prompt = f"""
    You are an expert at evaluating the semantic similarity between two texts. Your task is to compare a 'Required Data' text with a 'Candidate Data' text and provide a similarity score from 0 to 100.

    - A score of 100 means the two texts are semantically identical.
    - A score of 0 means they are completely unrelated.
    - If the 'Candidate Data' contains multiple items (e.g., a list of skills), your score should represent the best match found within that list.
    - Provide your response as a JSON object with a single key 'score' and its integer value.

    Required Data:
    ---
    {req_data}
    ---

    Candidate Data:
    ---
    {candidate_text}
    ---
    """
    
    try:
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        json_output = json.loads(response.text)
        score = json_output.get("score", 0)
        print(f"Generate content",score)
        return float(score), float(score)
    except Exception as e:
        print(f"Error computing score with Gemini: {e}")
        return 0.0, 0.0