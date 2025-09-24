from typing import Dict, Any, Type, List, Tuple
from pydantic import BaseModel
from ...plugins.base import BasePlugin,ExtractorPlugin, PluginMetadata, PluginCategory
from ...models import ResumeWorkExperience
from datetime import date
import logging

class ProjectExperiencePlugin(BasePlugin):
    """Extractor plugin for work experience information."""
    
    def __init__(self, llm_service):
        """Initialize the plugin with an LLM service."""
        self.llm_service = llm_service
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="project_experience",
            version="1.0.0",
            description="project_experience job",
            category=PluginCategory.CUSTOM,
            author="Resume Analysis Team"
        )
    
    def initialize(self) -> None:
        """Initialize the plugin."""
        logging.info(f"Initializing {self.metadata.name}")
    
    def get_model(self) -> Type[BaseModel]:
        """Get the Pydantic model for the extractor."""
        return ResumeWorkExperience
    
# You are an expert resume parser. Your task is to extract work experience details from the resume text provided below. For each work experience entry, extract the following details:
# Any sentence, line starting with date as specified under Date Parsing section below should be treated as new expereince entry.

# - Company
# - Start Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.
# - End Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.

# # - information: "string (raw text, including line breaks, bullet points, and original formatting)",all the information under this section which has Start Date and End Date as specified above should be extracted as string , this string will be calleed information and it should maintain the format as it is, like bold, new line etc.Strip out location,role,start_date,end_date from this string.

# # - information: "string (raw text, including line breaks, bullet points, and original formatting)". field MUST include a comprehensive summary of responsibilities, achievements, and FULL project details** that fall under this specific company's tenure.\n")
# - information: "string (raw text, including line breaks, bullet points, and original formatting)". field MUST include a comprehensive summary of responsibilities, achievements, and FULL project details** that fall under this specific company's tenure.\n")
#     # prompt_parts.append("    - The \"technologies\" array **MUST list ALL technologies explicitly mentioned as used within THIS role or its described projects**.\n\n")
 
#  **information**
#     * This is about what work has been done by person. Each such assignment, responsibiities are given for specific date ranges in a company.
#     * include all such information in this.
#     * It can include information about projects over a period of time in varioud roles, capacities
#  **Date Parsing:**
#     * **All dates must be converted and formatted to `DD/MM/YYYY`.**
#     * **Month Recognition:** Recognize full month names (e.g., "January", "Oct"), abbreviated month names (e.g., "Jan", "Oct"), and numerical months.
#     * **Day Default:** If the resume does not provide a specific day for a date (e.g., "October 2003", "Feb 2019"), default the day to "01".
#     * **Month Default (if only year present):** If the resume provides only the year (e.g., "2019"), default both the day and month to "01" (e.g., "01/01/2019").
#     * **End Date Keywords:** If you encounter 'Present', **'Till Date'**, 'Current', 'till now', or similar terms for an end date, use the current date: **07/06/2025**.
#     * **Date Range Separators:** Recognize common separators like "–", "-", "to", "till", "until".
    


# Return your output as a JSON object with the below schema.
# {format_instructions}

# Text:
# {text}
    
    
    def get_prompt_template(self) -> str:
        """Get the prompt template for the extractor."""
        return """
You are an expert resume parser. Your task is to extract work experience details from the resume text provided below. For each work experience entry, extract the following details:
Any sentence, line starting with date as specified under Date Parsing section below should be treated as new expereince entry.

- Company
- Start Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.
- End Date: in dd/mm/yyyy format. If the resume does not provide the day or month, default the missing parts to "01". If you encounter Present then use the current date, i.e. {today}.




- information: "string (raw text, including line breaks, bullet points, and original formatting)",all the information under this section which has Start Date and End Date as specified above should be extracted as string , this string will be calleed information and it should maintain the format as it is, like bold, new line etc.Strip out location,role,start_date,end_date from this string.

 
 **information**
    * This is about what work has been done by person. Each such project,assignment, responsibiities are given for specific date ranges in a company.
    * include all such information in this.
    * It can include information about projects over a period of time in varioud roles, capacities
    * Any description, summary given under Project, Assignments should be summaried under this.
 **Date Parsing:**
    * **All dates must be converted and formatted to `DD/MM/YYYY`.**
    * **Month Recognition:** Recognize full month names (e.g., "January", "Oct"), abbreviated month names (e.g., "Jan", "Oct"), and numerical months.
    * **Day Default:** If the resume does not provide a specific day for a date (e.g., "October 2003", "Feb 2019"), default the day to "01".
    * **Month Default (if only year present):** If the resume provides only the year (e.g., "2019"), default both the day and month to "01" (e.g., "01/01/2019").
    * **End Date Keywords:** If you encounter 'Present', **'Till Date'**, 'Current', 'till now', or similar terms for an end date, use the current date: **07/06/2025**.
    * **Date Range Separators:** Recognize common separators like "–", "-", "to", "till", "until".
    


Return your output as a JSON object with the below schema.
{format_instructions}

Text:
{text}
"""
    
    def get_input_variables(self) -> List[str]:
        """Get the input variables for the prompt template."""
        return ["text", "today"]
    
    def prepare_input_data(self, extracted_text: str) -> Dict[str, Any]:
        """Prepare the input data for the LLM."""
        return {
            "text": extracted_text,
            "today": date.today().strftime("%d/%m/%Y")
        }
    def process_resume(self, resume: Any, text: str) -> Dict[str, Any]:
    # def extract(self, text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract work experience information from text.
        
        Args:
            text: The text to extract information from.
            
        Returns:
            A tuple of (extracted_data, token_usage)
        """
        # Prepare prompt from template
        prompt_template = self.get_prompt_template()
        input_data = self.prepare_input_data(text)
        input_variables = self.get_input_variables()
        model = self.get_model()
        logging.debug(f"ProjectExpereince Called Extract {input_data}")
        # Call LLM service
        result, token_usage = self.llm_service.extract_with_llm(
            model,
            prompt_template,
            input_variables,
            input_data
        )
        logging.debug(f"ProjectExpereince data is {result}")
        # Add extractor name to token usage
        token_usage["extractor"] = self.metadata.name
        
        # Process the result to ensure it's a dict with the expected keys
        if isinstance(result, dict):
            processed_result = {
                "work_experiences": result.get("work_experiences", [])
            }
        else:
            # If result is a Pydantic model, convert to dict
            processed_result = {
                "work_experiences": getattr(result, "work_experiences", [])
            }
        
        # Ensure each work experience entry has expected fields
        for exp in processed_result["work_experiences"]:
            if isinstance(exp, dict):
                # Set default values for missing fields
                exp["company"] = exp.get("company") or ""
                exp["start_date"] = exp.get("start_date") or ""
                exp["end_date"] = exp.get("end_date") or ""
                exp["location"] = exp.get("location")  # Can be None
                exp["role"] = exp.get("role") or ""
        
        return processed_result, token_usage 