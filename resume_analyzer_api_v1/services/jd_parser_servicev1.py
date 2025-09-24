# services/jd_parser_service.py
# self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20') # Use stable model for JD parsing
import logging
import io
import json
import google.generativeai as genai
import os
import re
from typing import Dict, Any, Optional

from models.job_description_models import JobDescription, JobDetails 
from services.document_processor import DocumentProcessor 

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class JDParserServicev1:
    """
    Parses Job Description (JD) DOCX/PDF files into structured JSON using Gemini LLM.
    """
    def __init__(self, api_key: str, schema_path: str, prompt_template_path: str):
        if not api_key:
            logger.error("Gemini API Key not provided to JDParserService.")
            raise ValueError("Gemini API Key is required.")
        genai.configure(api_key=api_key)
        
        # self.gemini_model = genai.GenerativeModel('models/gemini-1.5-pro-latest') 
        self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20') # Use stable model for JD parsing
        logger.info(f"JDParserService initialized with Gemini model: {self.gemini_model.model_name}.")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.json_schema_string = f.read().strip()
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()
            logger.info(f"JD Prompt templates loaded from {schema_path} and {prompt_template_path}.")
        except FileNotFoundError as e:
            logger.error(f"JD Prompt template file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading JD prompt templates: {e}", exc_info=True)
            raise

    def parse_job_description(self, jd_file_stream: io.BytesIO) -> JobDescription:
        """
        Extracts text from JD file and parses it into a JobDescription Pydantic object.
        """
        try:
            jd_file_stream.seek(0) 
            processor = DocumentProcessor(jd_file_stream)
            raw_jd_text = processor.get_combined_document_content()
            logger.debug(f"Raw JD Text from DocumentProcessor (first 500 chars): {raw_jd_text[:500]}...")

            prompt = self._build_gemini_prompt(raw_jd_text)
            logger.debug(f"Gemini Prompt (first 500 chars): \n{prompt[:500]}...")

            # prompt = self.prompt_template.format(
            #     json_schema=self.json_schema_string,
            #     jd_text=raw_jd_text
            # )
            logger.debug(f"JD Parsing Prompt (first 500 chars): \n{prompt[:500]}...")

            response = self.gemini_model.generate_content(
                prompt
                # CRITICAL FIX: Explicitly set response_mime_type to application/json
                # generation_config={'response_mime_type': 'application/json'}
            )
            
            # The API might return the JSON string directly in .text or within specific parts
            # Check the response structure based on the Google Generative AI Python library's typical output.
            # If response_mime_type is set, .text should generally be the raw JSON string.
            json_string = response.text.strip() # This should be raw JSON now
            
            logger.info(f"Raw LLM JD Response ( chars) after response_mime_type: \n{json_string}...")

            # Clean up markdown fences and control characters (still good practice as fallback)
            match = re.search(r'^(```+json\s*|\s*)(.*?)(```+\s*)$', json_string, re.DOTALL | re.MULTILINE)
            if match:
                json_string = match.group(2).strip() 
                logger.info("Removed markdown fences from JD response.")
            else:
                logger.warning("No markdown fences found in JD response. Assuming direct JSON string.")
            
            json_string = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_string)
            json_string = json_string.strip().strip(',')

            logger.info(f"Cleaned LLM JD Response (first 500 chars): \n{json_string}...")

            parsed_jd_obj = JobDescription.model_validate_json(json_string) 
            logger.info("Gemini API JD parsing successful and Pydantic validation passed.")
            return parsed_jd_obj

        except json.JSONDecodeError as e:
            error_char_index = e.pos
            problematic_snippet = json_string[max(0, error_char_index - 100):min(len(json_string), error_char_index + 100)]
            logger.error(f"JSONDecodeError (JD parsing): {e}. Error at char {error_char_index}.")
            logger.error(f"Problematic JD JSON snippet: --> {problematic_snippet} <--", exc_info=True)
            raise ValueError(f"Failed to parse JD LLM response as JSON: {e}. Snippet: '{problematic_snippet}'")
        except Exception as e:
            logger.error(f"Error calling Gemini API (JD parsing) or parsing its response: {e}", exc_info=True)
            raise ValueError(f"Failed to parse JD with LLM: {e}. Check API key or prompt format.")

    # _build_main_parsing_prompt_from_template is not part of this class. It's for ResumeParserService.
    # The prompt_template is used directly here.
    
    
    def _build_gemini_prompt(self, resume_text):
        """Constructs the prompt for the Gemini LLM."""
        json_schema_string = """
{
  "job_title": "string",
  "location": "string",
  "employment_type": "string",
  "about_us": "string",
  "position_summary": "string",
  "key_responsibilities": ["string"],
  "required_qualifications": ["string"],
  "preferred_qualifications": ["string"],
  "what_we_offer": ["string"],
  "to_apply": "string",
  "equal_opportunity_employer_statement": "string (omit if not present)",
  "keywordmatch": 
    {
        "technical_skills": ["string"],
        "soft_skills": ["string"],
        "certifications": ["string"]  
    }
}
        """ # End of json_schema_string

        instructions_parts = []
 # Build the instructions part using prompt_parts.append
        instructions_parts = []
        instructions_parts.append("You are a highly skilled Job Description (JD) parser. Your task is to extract all relevant information from the provided job description text and return it in a structured JSON object.\n\n")
        instructions_parts.append("Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the JD text, omit that field from the JSON object.\n\n")
        instructions_parts.append("**Instructions for Extraction:**\n")
        instructions_parts.append("- \"job_title\": Extract the official Job Title:  field on document section.\n")
        instructions_parts.append("- \"location\": Extract the job's geographical location from Location: field on document.\n")
        instructions_parts.append("- \"employment_type\": Extract the employment type from Employment TYpe: field on document.\n")
        instructions_parts.append("- \"about_us\": Extract the company's \"About Us\" or About Us:  field on document.\n")
        instructions_parts.append("- \"position_summary\": Extract the Position Summary: field on document.\n")
        instructions_parts.append("- \"key_responsibilities\": Extract all Key Responsibilities : Section .\n")
        instructions_parts.append("- \"required_qualifications\": Extract all Required Qualifications from documet.\n")
        instructions_parts.append("- \"preferred_qualifications\": Extract all Preferred Qualification: from document\n")
        instructions_parts.append("- \"what_we_offer\": Extract from What We Offer: section\n")
        instructions_parts.append("- \"to_apply\": Extract To Apply : sectioin.\n")
        instructions_parts.append("- \"equal_opportunity_employer_statement\": Extract any Equal Opportunity Employer: from document.\n\n")
        
        instructions_parts.append("- \"technical_skills\": Extract all Technical Skills: section.\n\n")

        
        instructions_parts.append("- \"soft_skills\": Extract from Soft Skills: section.\n\n")
        instructions_parts.append("- \"certifications\": Extract from Certifications: section.\n\n")
        
        instructions_parts.append("Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.\n")

        instructions_parts.append("Desired JSON Schema:\n")
        instructions_parts.append("```json\n")
        instructions_parts.append(json_schema_string.strip() + "\n")
        instructions_parts.append("```\n\n")

        instructions_parts.append("Now, here is the resume text to parse:\n\n")
        instructions_parts.append("---\n")
        instructions_parts.append(resume_text + "\n")
        instructions_parts.append("---\n\n")
        instructions_parts.append("Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.\n")

        return "".join(instructions_parts)      