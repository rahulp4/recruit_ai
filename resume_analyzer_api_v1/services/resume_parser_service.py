import logging
import io
import json
from docx import Document
import google.generativeai as genai
import os
import re # ADD THIS IMPORT for more flexible regex cleaning

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ResumeParserService:
    """
    Handles DOCX text extraction and resume parsing using the Gemini LLM.
    """
    def __init__(self, api_key):
        if not api_key:
            logger.error("Gemini API Key not provided to ResumeParserService.")
            raise ValueError("Gemini API Key is required.")
        genai.configure(api_key=api_key)
        # self.gemini_model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
        
        # Stable
        # self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')
        self.gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # self.gemini_model = genai.GenerativeModel('models/gemini-2.0-flash') # Use stable model for JD parsing

        logger.info("ResumeParserService initialized with Gemini model.")

    def extract_text_from_docx(self, docx_file_stream):
        """Extracts all textual content from a .docx file stream."""
        try:
            document = Document(docx_file_stream)
            full_text = []
            for para in document.paragraphs:
                text = para.text.strip()
                if text:
                    full_text.append(text)
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}", exc_info=True)
            raise

    def parse_resume_with_gemini(self, resume_text):
        """
        Sends the resume text to the Gemini API for structured JSON extraction.
        """
        prompt = self._build_gemini_prompt(resume_text)
        logger.debug(f"Gemini Prompt (first 500 chars): \n{prompt[:500]}...")

        json_string = "" # Initialize json_string to ensure it's defined in the except block
        try:
            response = self.gemini_model.generate_content(prompt)
            json_string = response.text.strip()
            
            #logger.info(f"Raw LLM Response before cleaning (first 500 chars): \n{json_string[:500]}...")
            logger.info(f"Raw LLM Response before cleaning (first  chars): \n{json_string}...")
            match = re.search(r'^(```+json\s*|\s*)(.*?)(```+\s*)$', json_string, re.DOTALL | re.MULTILINE)
            if match:
                json_string = match.group(2).strip() 
                logger.info("Removed markdown fences.")
            else:
                json_match = re.search(r'\{.*\}', json_string, re.DOTALL)
                if json_match:
                    json_string = json_match.group(0)
                    logger.info("Extracted potential JSON object from the response.")
                else:
                    logger.warning("No markdown fences found and no clear JSON object detected. Attempting to parse raw string.")
            
            json_string = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_string)
            json_string = json_string.strip().strip(',')

            logger.info(f"LLM Response after cleaning (first 500 chars): \{json_string}...")

            parsed_data_dict = json.loads(json_string) 
            logger.info("Gemini API parsing successful.")
            return parsed_data_dict
        except json.JSONDecodeError as e: # Use 'e' as the exception object
            # Log the exact point of failure more clearly
            error_char_index = e.pos # Use e.pos
            context_window = 100 
            start_index = max(0, error_char_index - context_window)
            end_index = min(len(json_string), error_char_index + context_window)
            problematic_snippet = json_string[start_index:end_index]
            
            logger.error(f"JSONDecodeError: {e}. Error at char {error_char_index}.")
            logger.error(f"Problematic JSON snippet (around error): --> {problematic_snippet} <--")
            # Raise a new ValueError with the original error message and the snippet
            raise ValueError(f"Failed to parse LLM response as JSON: {e}. Snippet: '{problematic_snippet}'")
        except Exception as e:
            logger.error(f"Error calling Gemini API or parsing its response: {e}", exc_info=True)
            raise ValueError("Failed to parse resume with LLM. Check API key or prompt format.")

    def _build_gemini_prompt_BACK(self, resume_text):
        """Constructs the prompt for the Gemini LLM."""
        logger.info("HERE IT IS 1");
        json_schema_string = """
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
      "issuing_organization": "string (omit if not present)",
      "date": "string (01/MM/YYYY or descriptive like 'Completed')"
    }
  ]
}
        """ # End of json_schema_string

        prompt_parts = []
        prompt_parts.append("You are a highly skilled resume parser. Your task is to convert the following software engineer's resume text into a structured JSON object.\n\n")
        prompt_parts.append("Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the resume text, omit that field from the JSON object, unless it is part of a required sub-object.\n\n")
        prompt_parts.append("For all dates, ensure they are in the '01/MM/YYYY' format. If a date is 'Present' or 'Till Date', use 'Present'.\n\n")


        prompt_parts.append("**Specific Instructions for \"Experience\" Section (e.g., sections titled \"Experience\", \"Position & Company\", \"Work History\", or words meaning similar to these):**\n")
        # prompt_parts.append("- Create a distinct object in the \"experience\" array for EACH unique job role or employment period.\n")
        
        # WORKING BUT ALL EXPEREINCE IN SINGLE COMANY OBJECT-
        prompt_parts.append("- If multiple projects, create multiple object in the \"experience\" array for EACH expereince,employment period.\n")
        
        
        # prompt_parts.append("- If multiple experience,assingments, task, create multiple object in the \"experience\" array for EACH expereince,employment period.\n")
        
        prompt_parts.append("- **CRITICAL: If the experience is presented in, comma-separated line (like a CSV row or table in document or PDF) such as: `\"Job Title Company Name, Location Dates\",- Description`**\n")
        # prompt_parts.append("  - You MUST parse the initial quoted segment (e.g., `\"Lead Backend Engineer CloudNet Inc., Bengaluru Mar 2020 – Present\"`) to extract `title`, `company`, `location`, `from` date, and `to` date.\n")
        # prompt_parts.append("  - The text following the comma (e.g., `- Designed microservice architecture...`) belongs in the `description` field.\n")
        prompt_parts.append("- For each employment period:\n")
        prompt_parts.append("    - **MUST Extract the \"Designation\" or job role into the \"title\" field.** Provide a clear, concise title (e.g., \"Lead Backend Engineer\", \"Software Engineer\").\n")
        prompt_parts.append("    - **MUST Extract the \"Company Name\" into the \"company\" field.**\n")
        prompt_parts.append("    - **MUST Extract the \"Period\" into \"from\" and \"to\" date fields.**\n")
        prompt_parts.append("    - The \"description\" field **MUST include a comprehensive summary of responsibilities, achievements, and FULL project details** that fall under this specific company's tenure.\n")
        prompt_parts.append("    - The \"technologies\" array **MUST list ALL technologies explicitly mentioned as used within THIS role or its described projects**.\n\n")

        prompt_parts.append("**Specific Instructions for \"Skills\" or \"Technical Proficiencies\" Sections, especially if presented in a table:**\n")
        prompt_parts.append("- Categorize skills appropriately under 'languages', 'frameworks', 'databases', 'tools', 'platforms', 'methodologies', or 'other'.\n")
        prompt_parts.append("- If skills are listed with associated \"Years of Experience\" (e.g., in a table), extract both the skill \"name\" and \"experience_years\" (as a number) into the skill object. If years are not specified for a particular skill, omit the \"experience_years\" field.\n\n")
        
        
        
        prompt_parts.append("**Specific Instructions for \"Projects\" Section (top-level):**\n")
        prompt_parts.append("- Use the top-level \"projects\" array ONLY for standalone personal projects or academic projects that are NOT detailed as part of a specific company's experience.\n\n")

        prompt_parts.append("**Specific Instructions for \"Certifications\" Section:**\n")
        prompt_parts.append("- Extract all certifications with their names, issuing organizations (if clear), and dates (if present).\n\n")

        prompt_parts.append("Desired JSON Schema:\n")
        prompt_parts.append("```json\n")
        prompt_parts.append(json_schema_string.strip() + "\n")
        prompt_parts.append("```\n\n")

        prompt_parts.append("Now, here is the resume text to parse:\n\n")
        prompt_parts.append("---\n")
        prompt_parts.append(resume_text + "\n")
        prompt_parts.append("---\n\n")
        prompt_parts.append("Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.\n")

        return "".join(prompt_parts)      
    def _build_gemini_prompt_v2(self, resume_text):
        """Constructs the prompt for the Gemini LLM."""
        # Define the JSON schema part separately to avoid f-string/triple-quote confusion.
        # This string should be valid JSON if you were to parse it directly.


    def _build_gemini_prompt(self, resume_text):
        """Constructs the prompt for the Gemini LLM."""
        logger.info("HERE IT IS 2");
        json_schema_string = """
{
  "name": "string",
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string (URL, omit if not present)",
    "github": "string (URL, omit not present)",
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
      "technologies": ["string"],
      "nested_periods": [ {"description": "string", "from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"} ]
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
    "languages": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "frameworks": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "databases": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "tools": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "platforms": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "methodologies": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ],
    "other": [ { "name": "string", "experience_years": "number (omit if not specified)", "periods": [{"from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"}] } ]
  },
  "projects": [
    {
      "name": "string",
      "from": "string (01/MM/YYYY)",
      "to": "string (01/MM/YYYY or Present)",
      "description": "string (omit if not present)",
      "technologies": ["string"],
      "url": "string (URL, omit if not present)",
      "nested_periods": [ {"description": "string", "from": "string (01/MM/YYYY)", "to": "string (01/MM/YYYY or Present)"} ]
    }
  ],
  "certifications": [
    {
      "name": "string",
      "issuing_organization": "string (omit if not present)",
      "date": "string (01/MM/YYYY or descriptive like 'Completed')"
    }
  ]
}
        """ # End of json_schema_string

        prompt_parts = []
        prompt_parts.append("You are a highly skilled resume parser. Your task is to convert the following software engineer's resume text into a structured JSON object.\n\n")
        prompt_parts.append("Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the resume text, omit that field from the JSON object, unless it is part of a required sub-object.\n\n")
        prompt_parts.append("For all dates, ensure they are in the '01/MM/YYYY' format. If a date is 'Present' or 'Till Date', use 'Present'.\n\n")

        prompt_parts.append("**CRITICAL GENERAL INSTRUCTION FOR TABLES:**\n")
        prompt_parts.append("If the resume text contains data formatted in a table or multi-column layout (e.g., \"Skills & Experience Matrix\", \"IT Job Experience\", \"Position & Company\" tables), you MUST interpret each row as a distinct record. Extract data from each column of a row and associate it correctly within the corresponding JSON object. Use this extracted tabular data along with all other narrative data in the resume for comprehensive parsing.\n\n")

        # --- FEW-SHOT EXAMPLE START (for Experience Section - priyasharma.docx type format) ---
        prompt_parts.append("--- EXAMPLE START (Experience Section) ---\n")
        prompt_parts.append("Text:\n")
        prompt_parts.append("Experience\n\n")
        prompt_parts.append("Position & Company,Key Responsibilities & Achievements\n")
        prompt_parts.append("\"Lead Backend Engineer CloudNet Inc., Bengaluru Mar 2020 – Present\",- Designed microservice architecture for scalable platforms. - Migrated legacy systems to Spring Boot microservices on AWS. - Implemented CI/CD pipeline using Jenkins & Docker. - Led a backend team of 5 engineers.\n")
        prompt_parts.append("\"Software Engineer DataSolutions Ltd., Hyderabad Aug 2015 – Feb 2020\",- Developed REST APIs for internal and external clients. - Used Hibernate ORM for complex data mappings. - Integrated with third-party APIs and authentication providers. - Improved database query performance by 40%. \n")
        prompt_parts.append("Output JSON Snippet for 'experience' node:\n")
        prompt_parts.append("```json\n")
        prompt_parts.append("""
[
  {
    "title": "Lead Backend Engineer",
    "company": "CloudNet Inc.",
    "location": "Bengaluru",
    "from": "01/03/2020",
    "to": "Present",
    "description": "- Designed microservice architecture for scalable platforms. - Migrated legacy systems to Spring Boot microservices on AWS. - Implemented CI/CD pipeline using Jenkins & Docker. - Led a backend team of 5 engineers.",
    "technologies": ["Spring Boot", "Microservices", "AWS", "Jenkins", "Docker"],
    "nested_periods": []
  },
  {
    "title": "Software Engineer",
    "company": "DataSolutions Ltd.",
    "location": "Hyderabad",
    "from": "01/08/2015",
    "to": "01/02/2020",
    "description": "- Developed REST APIs for internal and external clients. - Used Hibernate ORM for complex data mappings. - Integrated with third-party APIs and authentication providers. - Improved database query performance by 40%.",
    "technologies": ["REST APIs", "Hibernate ORM", "Third-party APIs"],
    "nested_periods": []
  }
],
"achievements": ["string"]
""")
        prompt_parts.append("```\n")
        prompt_parts.append("--- EXAMPLE END ---\n\n")
        
           
        # CRITICAL FIX: General instruction for strict JSON formatting
        prompt_parts.append("**CRITICAL JSON FORMATTING INSTRUCTIONS:**\n")
        prompt_parts.append("- Ensure perfect JSON syntax. All keys and string values must be double-quoted.\n")
        prompt_parts.append("- Use commas to separate items in lists (arrays) and key-value pairs in objects.\n")
        prompt_parts.append("- DO NOT add a comma after the last item in a list or the last key-value pair in an object.\n")
        prompt_parts.append("- Use correct nesting of curly braces {} for objects and square brackets [] for arrays.\n")
        prompt_parts.append("- If a field is optional and no data is found, OMIT THE ENTIRE FIELD AND ITS KEY from the JSON object.\n")
        prompt_parts.append("- If an array is empty, provide an empty array `[]`.\n\n")

        prompt_parts.append("**Specific Instructions for \"Experience\" Section (e.g., sections titled \"Experience\", \"Position & Company\", \"Work History\", or words meaning similar to these):**\n")
        prompt_parts.append("- Create a distinct object in the \"experience\" array for EACH unique job role or employment period. Recognize patterns similar to the provided example.\n")
        prompt_parts.append("  - For each block:\n")
        prompt_parts.append("    - Extract the Job Title into the \"title\" field.\n")
        prompt_parts.append("    - Extract the Company Name into the \"company\" field.\n")
        prompt_parts.append("    - Extract the Location into the \"location\" field. Omit if not provided.\n")
        prompt_parts.append("    - Extract the \"from\" and \"to\" dates and format them to '01/MM/YYYY' or 'Present'.\n")
        prompt_parts.append("    - Extract the \"Key Responsibilities & Achievements\" text into the \"description\" field. Consolidate all bullet points or continuous text belonging to that role.\n")
        prompt_parts.append("    - Extract any explicit technologies, tools, or platforms mentioned within that role's description into the \"technologies\" array.\n")
        # NEW: Instructions for nested periods within Experience
        prompt_parts.append("- For the \"nested_periods\" array within each experience object:\n")
        prompt_parts.append("    - Identify any distinct projects, assignments, or significant phases that are described within the \"description\" field of that experience, AND that have their *own explicit timeframes* (e.g., \"Jan 2008 – Feb 2008\", \"Aug 2004 To Aug 2004\").\n")
        prompt_parts.append("    - For each such identified nested period, extract its specific \"description\" (what that period was about), \"from\" date, and \"to\" date into a `{\"description\": \"...\", \"from\": \"...\", \"to\": \"...\"}` object within the `nested_periods` array. Format dates as '01/MM/YYYY'.\n")
        prompt_parts.append("    - If no distinct nested periods with explicit timeframes are found for an experience, the `nested_periods` array should be empty for that entry.\n\n")


        prompt_parts.append("**Specific Instructions for \"Skills\" or \"Technical Proficiencies\" Sections, especially if presented in a table:**\n")
        prompt_parts.append("- Categorize skills appropriately under 'languages', 'frameworks', 'databases', 'tools', 'platforms', 'methodologies', or 'other'.\n")
        prompt_parts.append("- For each skill extracted:\n")
        prompt_parts.append("    - Extract the skill \"name\".\n")
        prompt_parts.append("    - If \"Years of Experience\" is explicitly listed for that skill (e.g., in a table), extract it as a number into the \"experience_years\" field.\n")
        prompt_parts.append("    - **CRITICAL: For the \"periods\" array within each skill object, identify ALL employment periods (from the \"experience\" section) where this skill was explicitly used or mentioned (in 'technologies' or 'description'). For each such *distinct job role/period of usage*, provide its exact 'from' and 'to' dates (matching the corresponding experience entry's dates) as a `{\"from\": \"...\", \"to\": \"...\"}` object within the 'periods' array. Do NOT aggregate or merge these periods in the LLM output; list them as separate entries if the skill was used in multiple distinct jobs. If no specific usage periods can be clearly identified for a skill, the \"periods\" array should be empty.**\n\n")

        prompt_parts.append("**Specific Instructions for \"Projects\" Section (top-level):**\n")
        prompt_parts.append("- Use the top-level \"projects\" array ONLY for standalone personal projects or academic projects that are NOT detailed as part of a specific company's experience.\n")
        # NEW: Instructions for nested periods within Projects
        prompt_parts.append("- For the \"nested_periods\" array within each project object:\n")
        prompt_parts.append("    - Identify any distinct phases or assignments within the project's description that have *their own explicit timeframes*. Extract their \"description\", \"from\" date, and \"to\" date into an object in the `nested_periods` array.\n")
        prompt_parts.append("    - If no distinct nested periods with explicit timeframes are found for a project, the `nested_periods` array should be empty.\n\n")


        prompt_parts.append("**Specific Instructions for \"Certifications\" Section:**\n")
        prompt_parts.append("- Extract all certifications with their names, issuing organizations (if clear), and dates (if present).\n\n")


        prompt_parts.append("**Specific Instructions for \"Achievements\" Section:")

        prompt_parts.append("-If there is a section titled \"Achievements\", \"Key Achievements\", \"Awards\", \"Accomplishments\", or similar, extract each distinct achievement as a separate string into the \"achievements\" array. List them exactly as they appear (e.g., \"Recognized as 'Infrastructure Innovator of the Year'")

        prompt_parts.append("Desired JSON Schema:\n")
        prompt_parts.append("```json\n")
        prompt_parts.append(json_schema_string.strip() + "\n")
        prompt_parts.append("```\n\n")

        prompt_parts.append("Now, here is the resume text to parse:\n\n")
        prompt_parts.append("---\n")
        prompt_parts.append(resume_text + "\n")
        prompt_parts.append("---\n\n")
        prompt_parts.append("Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.\n")

        return "".join(prompt_parts)
      
    def _build_gemini_prompt_v1(self, resume_text):
        """Constructs the prompt for the Gemini LLM."""
        json_schema_string = """
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
              "issuing_organization": "string (omit if not present)",
              "date": "string (01/MM/YYYY or descriptive like 'Completed')"
            }
          ]
        }
                """ # End of json_schema_string

        # Construct the final prompt using the schema string.
        prompt = f"""You are a highly skilled resume parser. Your task is to convert the following software engineer's resume text into a structured JSON object.

          Strictly adhere to the following JSON schema. If a field's value is not explicitly present in the resume text, omit that field from the JSON object, unless it is part of a required sub-object.

          For all dates, ensure they are in the '01/MM/YYYY' format. If a date is 'Present' or 'Till Date', use 'Present'.

          **Specific Instructions for "Experience" Section (e.g., sections titled "Experience", "Position & Company", "Work History", or words meaning similar to these):**
          - Create a distinct object in the "experience" array for EACH unique job role or employment period.
          - Recognize patterns where:
              - A Job Title (e.g., "Lead Backend Engineer", "Software Engineer") is followed by a Company Name and Location (e.g., "CloudNet Inc., Bengaluru").
              - Then, a Date Range (e.g., "Mar 2020 – Present").
              - Followed by bullet points or descriptive text for "Key Responsibilities & Achievements".
          - For each such block:
              - Extract the Job Title (e.g., "Lead Backend Engineer") into the "title" field.
              - Extract the Company Name (e.g., "CloudNet Inc.") into the "company" field.
              - Extract the Location (e.g., "Bengaluru") into the "location" field. Omit if not provided.
              - Extract the "from" and "to" dates (e.g., "Mar 2020", "Present") and format them to '01/MM/YYYY' or 'Present'.
              - Extract the "Key Responsibilities & Achievements" text into the "description" field. Consolidate all bullet points or continuous text belonging to that role.
              - Extract any explicit technologies, tools, or platforms mentioned within that role's description into the "technologies" array.

          **Specific Instructions for "Skills" or "Technical Proficiencies" Sections:**
          - Categorize skills appropriately under 'languages', 'frameworks', 'databases', 'tools', 'platforms', 'methodologies', or 'other'.
          - If skills are listed with associated "Years of Experience" (e.g., in a table), extract both the skill "name" and "experience_years" (as a number) into the skill object. If years are not specified for a particular skill, omit the "experience_years" field.

          **Specific Instructions for "Projects" Section (top-level):**
          - Use the top-level "projects" array ONLY for standalone personal projects or academic projects.

          **Specific Instructions for "Certifications" Section:**
          - Extract all certifications with their names, issuing organizations (if clear), and dates (if present).

          Desired JSON Schema:
          ```json

        {json_schema_string.strip()}

        Now, here is the resume text to parse:

        ---
        {resume_text}
        ---

        Return ONLY the JSON object. Do not include any other text, explanations, or markdown outside of the JSON block.
        """
        return prompt