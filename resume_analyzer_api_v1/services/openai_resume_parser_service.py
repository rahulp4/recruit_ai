import logging
import json
import re
from docx import Document
from openai import OpenAI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class OpenAIResumeParserService:
    """
    Handles DOCX text extraction and resume parsing using OpenAI GPT models (SDK >= 1.0.0).
    """

    def __init__(self):
        # if not api_key:
        #     logger.error("OpenAI API Key not provided to ResumeParserService.")
        #     raise ValueError("OpenAI API Key is required.")
        self.client = OpenAI(api_key="<<>>")
        logger.info("ResumeParserService initialized with OpenAI SDK >= 1.0.0.")

    def extract_text_from_docx(self, docx_file_stream):
        """
        Extracts all textual content from a .docx file stream.
        """
        try:
            document = Document(docx_file_stream)
            full_text = [para.text.strip() for para in document.paragraphs if para.text.strip()]
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}", exc_info=True)
            raise

    def parse_resume_with_openai(self, resume_text):
        """
        Sends the resume text to OpenAI GPT-4o for structured JSON extraction.
        """
        prompt = self._build_openai_prompt(resume_text)
        logger.debug(f"Prompt (first 500 chars): \n{prompt[:500]}")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a resume parser that outputs structured JSON from resume text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            json_string = response.choices[0].message.content.strip()

            # Extract JSON from ```json ... ``` if present
            match = re.search(r'^```(?:json)?\s*(.*?)```$', json_string, re.DOTALL)
            if match:
                json_string = match.group(1).strip()
                logger.info("Stripped markdown-style JSON block.")

            # Remove unprintable characters
            json_string = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_string).strip().strip(',')

            parsed_data = json.loads(json_string)
            logger.info("Resume parsing successful.")
            return parsed_data

        except json.JSONDecodeError as e:
            start, end = max(0, e.pos - 100), e.pos + 100
            logger.error(f"JSONDecodeError at position {e.pos}: {e}")
            logger.error(f"Snippet near error: --> {json_string[start:end]} <--")
            raise ValueError(f"Failed to parse JSON from OpenAI response: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise ValueError("Failed to parse resume with OpenAI.")

    def _build_openai_prompt(self, resume_text):
        """
        Constructs the prompt using the required JSON schema and resume text.
        """
        schema = """
{
  "name": "string",
  "contact": {
    "email": "string",
    "phone": "string",
    "linkedin": "string (omit if not present)",
    "github": "string (omit if not present)",
    "website": "string (omit if not present)",
    "location": "string (omit if not present)"
  },
  "summary": "string",
  "total_experience_years": "number (omit if not explicitly stated)",
  "experience": [
    {
      "title": "string",
      "company": "string",
      "location": "string (omit if not present)",
      "from": "string (01/MM/YYYY)",
      "to": "string (01/MM/YYYY or Present)",
      "description": "string",
      "technologies": ["string"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "field_of_study": "string (omit if not present)",
      "institution": "string",
      "location": "string (omit if not present)",
      "dates": "string"
    }
  ],
  "skills": {
    "languages": [
      {
        "name": "string",
        "experience_years": "number (omit if not specified)",
        "from": "string (01/MM/YYYY)",
        "to": "string (01/MM/YYYY or Present)"
      }
    ],
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
      "url": "string (omit if not present)"
    }
  ],
  "certifications": [
    {
      "name": "string",
      "issuing_organization": "string (omit if not present)",
      "date": "string"
    }
  ]
}
        """.strip()

        return f"""
You are a highly skilled resume parser. Your task is to convert the following resume into a structured JSON object.

Strictly follow the schema below. Omit fields not explicitly present in the resume. Format all dates as '01/MM/YYYY' or 'Present'.

Schema:
```json
{schema}
"""