from typing import Dict, List, Any, Tuple, Type
from pydantic import BaseModel
from ...models.resume_models import ResumeProfile
from ...plugins.base import ExtractorPlugin, PluginMetadata, PluginCategory
import logging

class ProfileExtractorPlugin(ExtractorPlugin):
    """Plugin for extracting profile information from resumes."""
    
    def __init__(self, llm_service=None):
        """
        Initialize the plugin with an LLM service.
        
        Args:
            llm_service: LLM service for extracting information
        """
        self.llm_service = llm_service
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="profile_extractor",
            version="1.0.0",
            description="Extracts basic profile information from resumes",
            category=PluginCategory.BASE,
            author="Resume Analysis Team"
        )
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logging.info(f"Initializing {self.metadata.name}")
    
    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the extractor."""
        return ResumeProfile
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for the extractor."""
        return """
You are an expert resume parser. Your task is to extract the contact information from the resume text provided below. Specifically, extract the following details:
- Name: Name of the candidate
- Email: The candidate's email address
- Phone: The candidate's phone number,contact number including country code if present
- LinkedIn: LinkedIn profile URL if present
- Current Title: The candidate's current job title if present
- Summary: A brief summary or objective statement if present.

If any of these fields are not present in the resume, return null for that field

Return your output as a JSON object with the below schema
{format_instructions}

Text:
{text}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["text"]
    
    def prepare_input_data(self, extracted_text: str) -> Dict[str, Any]:
        """Prepare the input data for the LLM."""
        return {"text": extracted_text}
    
    def extract(self, text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract profile information from text.
        
        Args:
            text: The text to extract information from.
            
        Returns:
            A tuple of (extracted_data, token_usage)
        """
        # Prepare prompt from template
        # prompt_template = self.get_prompt_template()
        prompt_template = self.get_prompt_templatev1()
        input_data = self.prepare_input_data(text)
        input_variables = self.get_input_variables()
        model = self.get_model()
        
        # Call LLM service
        result, token_usage = self.llm_service.extract_with_llm(
            model,
            prompt_template,
            input_variables,
            input_data
        )
        
        logging.debug(f"ProfileExtraction as {result}");
        # Add extractor name to token usage
        token_usage["extractor"] = self.metadata.name
        
        # Process the result
        fields = ["name", "email", "phone", "linkedin", "current_title", "summary"]
        processed_result = {}
        
        if isinstance(result, dict):
            for field in fields:
                processed_result[field] = result.get(field)
        else:
            for field in fields:
                processed_result[field] = getattr(result, field, None)
                
        logging.debug(f"ProfileExtraction as Processes {processed_result}");                
        return processed_result, token_usage
    
    

    def get_prompt_templatev1(self) -> str:
        """Get the prompt template for the extractor."""
        
        format_instructions = """
        {
        "name": "string",
        "contact": {
            "email": "string",
            "phone": "string",
            "linkedin": "string (URL, omit if not present)",
            "github": "string (URL, omit if not present)",
            "website": "string (URL, omit if not present)",
            "location": "string (omit if not present)"
        },
        "summary": "string",
        "total_experience_years": "number (extract if explicitly mentioned like 'X years of experience', otherwise omit)",
        "experience": [
            {
            "title": "string",
            "company": "string",
            "location": "string (omit if not present)",
            "from": "string (01/MM/YYYY)",
            "to": "string (01/MM/YYYY or Present)",
            "description": "string (omit if not present)",
            "technologies": ["string"]
            }
        ],
        "education": [
            {
            "degree": "string",
            "field_of_study": "string (omit if not present)",
            "institution": "string",
            "location": "string (omit if not present)",
            "dates": "string (01/MM/YYYY, Present, or descriptive like 'Passed with 69%')"
            }
        ],
        "skills": {
            "languages": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "frameworks": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "databases": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "tools": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "platforms": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "methodologies": [ { "name": "string", "experience_years": "number (omit if not specified)" } ],
            "other": [ { "name": "string", "experience_years": "number (omit if not specified)" } ]
        },
        "projects": [
            {
            "name": "string",
            "from": "string (01/MM/YYYY)",
            "to": "string (01/MM/YYYY or Present)",
            "description": "string (omit if not present)",
            "technologies": ["string"],
            "url": "string (URL, omit if not present)"
            }
        ],
        "certifications": [
            {
            "name": "string",
            "issuing_organization": "string (URL, omit if not present)",
            "date": "string (01/MM/YYYY or descriptive like 'Completed')"
            }
        ]
        }"""        
        return """
    You are a highly skilled resume parser. Your task is to convert the following software engineer's resume text into a structured JSON object.

        Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the resume text, omit that field from the JSON object, unless it is part of a required sub-object.

        For all dates, ensure they are in the '01/MM/YYYY' format. If a date is 'Present' or 'Till Date', use 'Present'. If a date is like 'Passed with 69%', keep it as is.



        **Specific Instructions for "Experience" Section (e.g., sections titled "IT Job Experience", "Work History", or similar):**
        - Create a distinct object in the "experience" array for EACH employment period listed. For example, if the resume lists roles at "Oracle Financial Software Services", "WIPRO Technologies", and "L and T Infotech Limited", ensure ALL THREE are captured as separate objects in the "experience" array.
            - If you come across section starting with Expereince,Expereinces or words having similar meaning and find timeline dates,create a expereince array data from it.
              For example, section may start with Expereince and below might be company name and positions, roles,responsibilities. This can be treated as expereince.
        - For each employment period:
            - Extract the "Designation" or job role into the "title" field (e.g., "Director (Product Dev)", "Project Engineer", "Sr Software Engineer"). If a title is clearly associated with a company and period, extract it.
            - Extract the "Company Name" into the "company" field.
            - Extract the "Period" (e.g., "October 2003 Till Date", "Jan 1999 Till April 2003") into "from" and "to" date fields.
            - The "description" field for an experience entry should include a summary of responsibilities and any project details mentioned *under that specific company's tenure*. For example, if a "Project Experience" section details work done at "Oracle Financial Software Services", that text belongs in the "description" of the relevant "Oracle Financial Software Services" experience entry. Similarly, for "L and T Infotech Limited", include summaries of projects like "KeyService for public, private and Symmetric keys", "CANSYS Claims Management System", etc., within its "description" field.
            - The "technologies" array within an experience object should ONLY list technologies explicitly mentioned as used *during that specific role or on projects described under that role*. Look for "Technology :" labels or lists embedded in the role's description or project details. For example, for the "L and T Infotech" role, extract technologies mentioned for specific projects like "KeyService" (e.g., "Weblogic81", "Java Webservices", "SOAP") or "CANSYS" into this array.

        **Specific Instructions for "Skills" or "Technical Proficiencies" Sections (especially if presented in a table):**
        - If skills are listed with associated "Years of Experience" in a table, extract both the skill "name" and "experience_years" (as a number) into the skill object. If years are not specified for a skill, omit "experience_years".
        - Categorize all extracted skills appropriately under 'languages', 'frameworks', 'databases', 'tools', 'platforms', 'methodologies', or 'other'.

        **Specific Instructions for "Projects" Section (top-level):**
        - Use the top-level "projects" array ONLY for standalone personal projects or academic projects that are NOT detailed as part of a specific company's experience. Projects done *at* a company should be part of that company's "experience[].description" and their technologies in "experience[].technologies". For the "Rahul_Poddar_V4.docx", most projects described are part of his company experience.


Return your output as a JSON object with the below schema
{format_instructions}

Text:
{text}
"""    