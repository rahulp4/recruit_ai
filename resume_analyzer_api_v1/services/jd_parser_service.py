import logging
import io
import json
import google.generativeai as genai
import os
import re
from typing import Dict, Any, Optional

from models.job_description_models import JobDescription, BaseRuleConfig, JobTitleRule, LocationRule, EmploymentTypeRule, AboutUsRule, PositionSummaryRule, KeyResponsibilitiesRule, RequiredQualificationsRule, PreferredQualificationsRule, DegreeRule, FieldOfStudyRule, OrganizationSwitchesRule, CurrentTitleRule 

from services.document_processor import DocumentProcessor 

logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO) # Inherit from root or set explicitly

class JDParserService:
    """
    Parses Job Description (JD) DOCX/PDF files into a structured JSON
    defining matching rules, using Gemini LLM. The prompt is embedded.
    """
    def __init__(self, api_key: str, schema_path: str, prompt_template_path: str): # schema_path and prompt_template_path are loaded but not used by _build_gemini_prompt if content is hardcoded
        if not api_key:
            logger.error("Gemini API Key not provided to JDParserService.")
            raise ValueError("Gemini API Key is required.")
        genai.configure(api_key=api_key)
        
        # self.gemini_model = genai.GenerativeModel('models/gemini-1.5-pro-latest') # Using 1.5-pro-latest for stability with structured output
        # self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20') # Use stable model for JD parsing
        self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash') # Use stable model for JD parsing
        logger.info(f"JDParserService initialized with Gemini model: {self.gemini_model.model_name}.")
        
        try:
            # json_schema_string is still loaded from the file, but its content is duplicated in _build_gemini_prompt
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.json_schema_string_from_file = f.read().strip() # Store as distinct name to avoid confusion
            # self.prompt_template is not used if _build_gemini_prompt hardcodes
            # with open(prompt_template_path, 'r', encoding='utf-8') as f:
            #     self.prompt_template_file_content = f.read()
            logger.info(f"JD Prompt templates loaded (schema from {schema_path}).")
        except FileNotFoundError as e:
            logger.error(f"JD Schema file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading JD schema: {e}", exc_info=True)
            raise

    def parse_job_description(self, jd_file_stream: io.BytesIO) -> JobDescription: # Returns JobDescription object (which is the rule-based one)
        """
        Extracts text from JD file and parses it into a JobMatchingRules Pydantic object.
        """
        try:
            jd_file_stream.seek(0) 
            processor = DocumentProcessor(jd_file_stream)
            raw_jd_text = processor.get_combined_document_content()
            logger.debug(f"Raw JD Text from DocumentProcessor (first 500 chars): {raw_jd_text[:500]}...")

            prompt = self._build_gemini_prompt(raw_jd_text) # This will correctly assemble the prompt
            logger.debug(f"JD Parsing Prompt (first 500 chars): \n{prompt}...")

            response = self.gemini_model.generate_content(
                prompt,
                generation_config={'response_mime_type': 'application/json'} 
            )
            
            json_string = response.text.strip()
            
            logger.info(f"Raw LLM JD Response (first 500 chars) after response_mime_type: \n{json_string[:500]}...")

            match = re.search(r'^(```+json\s*|\s*)(.*?)(```+\s*)$', json_string, re.DOTALL | re.MULTILINE)
            if match:
                json_string = match.group(2).strip() 
                logger.info("Removed markdown fences from JD response.")
            else:
                logger.warning("No markdown fences found in JD response. Assuming direct JSON string.")
            
            json_string = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_string)
            json_string = json_string.strip().strip(',')

            logger.info(f"Cleaned LLM JD Response : \n{json_string}...")

            parsed_jd_obj = JobDescription.model_validate_json(json_string) 
            logger.info("Gemini API JD parsing successful and Pydantic validation passed against JobDescription (rule-based).")
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

    # _build_gemini_prompt method, with instructions directly embedded via prompt_parts
    def _build_gemini_prompt(self, jd_text: str):
        """
        Constructs the prompt for the Gemini LLM by concatenating string parts,
        with specific instructions and schema hardcoded here.
        """
        # This json_schema_string is hardcoded here, effectively overriding the one loaded in __init__.
        # This is the current state you provided.
        json_schema_string = """
{
  "job_title": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "profiledatasource": ["string"],
    "data": ["string"]
  },
  "location": {
    "type": "str",
    "fromsource":"string"
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "sourcecondition": "string (OR or AND)",
    "profiledatasource": ["string"],
    "data": ["string"]
  },
  "employment_type": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "data": ["string"]
  },
  "about_us": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (vector)",
    "profiledatasource": ["string"],
    "data": "string"
  },
  "position_summary": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (vector)",
    "profiledatasource": ["string"],
    "data": "string"
  },
  "key_responsibilities": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (vector)",
    "profiledatasource": ["string"],
    "data": "string"
  },
  "required_qualifications": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (vector)",
    "profiledatasource": ["string"],
    "data": "string"
  },
  "preferred_qualifications": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (vector)",
    "sourcecondition":"OR"
    "profiledatasource": ["string"],
    "data": "string"
  },
  "degree": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "sourcecondition": "string (OR or AND)",
    "profiledatasource": ["string"],
    "data": ["string"]
  },
  "field_of_study": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "profiledatasource": ["string"],
    "data": "string"
  },
  "organization_switches": {
    "type": "num",
    "weightage": "number (0-5)",
    "matchreq": "string (operator)",
    "profiledatasource": ["string"],
    "data": "string (e.g., '<3', '>5', '=2')"
  },
  "current_title": {
    "type": "str",
    "weightage": "number (0-5)",
    "matchreq": "string (jaccard or vector)",
    "profiledatasource": ["string"],
    "data": ["string"]
  },
   "keywordmatch": 
    {
        "technical_skills": {
            "type": "str",
            "weightage": "number (0-5)",
            "matchreq": "string (jaccard or vector)",
            "profiledatasource": ["string"],
            "data": ["string"]
        },
        "soft_skills":{
            "type": "str",
            "weightage": "number (0-5)",
            "matchreq": "string (jaccard or vector)",
            "profiledatasource": ["string"],
            "data": ["string"]
        },
        "certifications":{
            "type": "str",
            "weightage": "number (0-5)",
            "matchreq": "string (jaccard or vector)",
            "profiledatasource": ["string"],
            "data": ["string"]
        }  
    }
}
        """ # End of json_schema_string

        prompt_parts = []
        prompt_parts.append("You are a highly skilled Job Description (JD) parser. Your task is to extract all relevant information from the provided job description text and return it in a structured JSON object.\n\n")
        prompt_parts.append("Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the JD text, omit that field from the JSON object.\n\n")
        
        prompt_parts.append("**General Rules for Each Extracted Field:**\n")
        prompt_parts.append("- Every field in the output JSON (e.g., \"job_title\", \"location\", \"position_summary\") represents a rule.\n")
        prompt_parts.append("- Each rule object MUST contain:\n")
        prompt_parts.append("  - \"type\": \"str\" for string-based comparisons, \"num\" for numeric comparisons.\n")
        prompt_parts.append("  - \"weightage\": An integer from 0 to 5, indicating its importance (5 is highest). Infer based on prominence and typical job importance.\n")
        prompt_parts.append("  - \"matchreq\": The matching strategy:\n")
        prompt_parts.append("    - \"jaccard\": For keyword/phrase matching, good for specific lists (e.g., job titles, locations, degrees, current_title keywords).\n")
        prompt_parts.append("    - \"vector\": For semantic similarity, good for long descriptive fields (e.g., summaries, responsibilities, qualifications).\n")
        prompt_parts.append("    - \"operator\": For numeric comparisons (e.g., organization_switches, experience_years).\n")
        prompt_parts.append("  - \"profiledatasource\": A list of one or more dot-notation strings indicating paths in the candidate profile JSON where this rule's data should be checked (e.g., \"experience.title\", \"summary\", \"organization_switches\").\n")
        prompt_parts.append("  - \"data\": This is the VALUE to match against.\n")
        prompt_parts.append("    - For \"jaccard\" matchreq: This should be a LIST of keywords or phrases extracted from the JD.\n")
        prompt_parts.append("    - For \"vector\" matchreq: This should be a SINGLE string, the full extracted text from the JD for that section.\n")
        prompt_parts.append("    - For \"operator\" matchreq: This should be a SINGLE string representing the numeric condition (e.g., \"<3\", \">5\", \"=2\").\n")
        prompt_parts.append("  - \"sourcecondition\": (Optional, for \"jaccard\" rules with multiple data sources) \"OR\" or \"AND\" to combine profiledatasource checks.\n\n")

        prompt_parts.append("**Specific Extraction Instructions for Each Rule's 'data' Field:**\n")
        prompt_parts.append("- \"job_title\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"experience.title\", \"current_title\"]\n")
        prompt_parts.append("  - `data`: Extract a list of key phrases/words from the official job title.\n")
        prompt_parts.append("- \"location\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"contact.location\"]\n")
        prompt_parts.append("  - `data`: Extract a list of primary locations mentioned.\n")
        prompt_parts.append("  - `fromsource`: Extract locations from.\n")
        
        prompt_parts.append("  - `sourcecondition`: \"OR\"\n")
        prompt_parts.append("- \"employment_type\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"employment_type\"]\n")
        prompt_parts.append("  - `data`: Extract the employment type (e.g., \"Full-time\", \"Part-time\") as a LIST of strings. For a single type, return a list with one item (e.g., [\"Full-time\"]).\n") # FIX IS HERE
        prompt_parts.append("- \"about_us\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"vector\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"summary\"]\n")
        prompt_parts.append("  - `data`: Extract the full \"About Us\" statement.\n")
        prompt_parts.append("- \"position_summary\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"vector\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"experience.description\", \"summary\", \"experience.technologies\"]\n")
        prompt_parts.append("  - `data`: Extract the full \"Position Summary\" text.\n")
        prompt_parts.append("- \"key_responsibilities\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"vector\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"experience.description\", \"summary\"]\n")
        prompt_parts.append("  - `data`: Extract the full text of \"Key Responsibilities\" or similar sections as a single string.\n")
        prompt_parts.append("- \"required_qualifications\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"vector\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"experience.description\", \"summary\", \"skills.languages.name\", \"skills.frameworks.name\", \"skills.tools.name\", \"skills.platforms.name\", \"certifications.name\"]\n")
        prompt_parts.append("  - `data`: Extract the full text of \"Required Qualifications\" or similar sections as a single string.\n")
        prompt_parts.append("- \"preferred_qualifications\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"vector\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"experience.description\", [\"experience.nested_periods.description\",\"summary\", \"skills.languages.name\", \"skills.frameworks.name\", \"skills.tools.name\", \"skills.platforms.name\", \"certifications.name\"]\n")
        prompt_parts.append("  - `data`: Extract the full text of \"Preferred Qualifications\" or similar sections as a single string.\n")
        prompt_parts.append("- \"degree\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"education.degree\", \"education.field_of_study\"]\n")
        prompt_parts.append("  - `data`: Extract a list of required/preferred degree types or fields of study.\n")
        prompt_parts.append("  - `sourcecondition`: \"OR\"\n")
        prompt_parts.append("- \"field_of_study\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"education.field_of_study\"]\n")
        prompt_parts.append("  - `data`: Extract a specific field of study as a string.\n")
        prompt_parts.append("- \"organization_switches\":\n")
        prompt_parts.append("  - `type`: \"num\"\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"operator\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"organization_switches\"]\n")
        prompt_parts.append("  - `data`: Extract the numeric condition (e.g., \"<3\", \">5\", \"=2\") for organization switches.\n")
        prompt_parts.append("- \"current_title\":\n")
        prompt_parts.append("  - `weightage`: Infer based on JD.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"current_title\"]\n")
        prompt_parts.append("  - `data`: Extract a list of keywords/phrases from the desired current job title.\n\n")

 # NEW: Specific Instructions for "keywordmatch" Section
        prompt_parts.append("**Specific Instructions for \"keywordmatch\" Section (for categorized keywords):**\n")
        prompt_parts.append("- This section defines rules for categorized keywords that should be extracted and used in matching.\n")
        prompt_parts.append("- \"technical_skills\": Extract a LIST of primary technical skills mentioned in the JD.\n")
        prompt_parts.append("  - `type`: \"str\"\n")
        prompt_parts.append("  - `weightage`: Infer importance.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"skills.languages.name\", \"skills.frameworks.name\", \"skills.tools.name\", \"skills.platforms.name\", \"experience.technologies\"]\n")
        prompt_parts.append("  - `data`: List of extracted technical skill keywords.\n")
        prompt_parts.append("- \"soft_skills\": Extract a LIST of soft skills implied or explicitly mentioned.\n")
        prompt_parts.append("  - `type`: \"str\"\n")
        prompt_parts.append("  - `weightage`: Infer importance.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"summary\", \"experience.description\"]\n")
        prompt_parts.append("  - `data`: List of extracted soft skill keywords.\n")
        prompt_parts.append("- \"certifications\": Extract a LIST of any certifications mentioned or implied.\n")
        prompt_parts.append("  - `type`: \"str\"\n")
        prompt_parts.append("  - `weightage`: Infer importance.\n")
        prompt_parts.append("  - `matchreq`: \"jaccard\"\n")
        prompt_parts.append("  - `profiledatasource`: [\"certifications.name\"]\n")
        prompt_parts.append("  - `data`: List of extracted certification keywords.\n\n")


        prompt_parts.append("Desired JSON Schema:\n")
        prompt_parts.append("```json\n")
        prompt_parts.append(json_schema_string.strip() + "\n")
        prompt_parts.append("```\n\n")

        prompt_parts.append("Now, here is the Job Description text to parse:\n\n")
        prompt_parts.append("---\n")
        prompt_parts.append(jd_text + "\n")
        prompt_parts.append("---\n\n")
        prompt_parts.append("Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.\n")

        return "".join(prompt_parts)