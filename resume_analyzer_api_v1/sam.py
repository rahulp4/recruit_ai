import os
import json
from dotenv import load_dotenv
from matchai import MatchAIClient
from matchai.custom_plugins.project_experience import ProjectExperiencePlugin
from matchai.core.utils.logging_utils import setup_logging
# Change here
# from custom_plugins  import ProjectExperiencePlugin
# Load API key from .env file if available
load_dotenv()
setup_logging()

# Get API key from environment or prompt
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    api_key = input("Enter your Gemini API key: ")

# Initialize client with API key
client = MatchAIClient(api_key=api_key)
# resume_path = "/Users/rahulpoddar/my-work/project_resumev2/trials/MatchAI/Resumes/Gaurav_Kumar.docx"
resume_path = "/Users/rahulpoddar/my-work/project_resume/resume_structurer_llm/sample_data/Rahul_Poddar_V4.docx"

# resume_path = "/Users/rahulpoddar/my-work/project_resume/resume_structurer_llm/sample_data/priyasharma.docx"
# resume_path = "/Users/rahulpoddar/my-work/project_resume/resume_structurer_llm/sample_data/Software_Engineer_10Y_Profile.docx"
# resume_path = "/Users/rahulpoddar/my-work/project_resume/resume_structurer_llm/sample_data/jb.docx"
# resume_path = "/Users/rahulpoddar/my-work/project_resume/resume_structurer_llm/sample_data/Vikram_Manufac.docx"
# resume_path = "/Users/rahulpoddar/fyndna/development/GenerativeAI/Rahul_Poddar_V4.docx"
# resume_path = "/Users/rahulpoddar/fyndna/development/GenerativeAI/Vikram.docx"
# resume_path = "/Users/rahulpoddar/fyndna/development/GenerativeAI/PritiResume.pdf"
# resume_path = "/Users/rahulpoddar/fyndna/development/GenerativeAI/KG.pdf"
# Extract and print years of experience
# print("Years of experience:", client.extract_years_of_experience(resume_path))

# Extract and print skills as formatted JSON
# skills = client.extract_skills(resume_path)
# print("\nSkills:")
# print(json.dumps(skills, indent=2))


# custom_plugin = ProjectExperiencePlugin()
# custom_plugin.process_output
# client._plugin_manager.register_plugin(custom_plugin)



# Extract all information (token usage logged separately to logs/ directory)
result = client.extract_all(resume_path, log_token_usage=True)
print("\nFull resume information:")
print(json.dumps(result, indent=2))