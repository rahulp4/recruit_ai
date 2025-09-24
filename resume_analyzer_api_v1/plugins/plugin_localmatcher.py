
from .localmatcher.localmatcher import ProfileMatcher
import json

from plugin_registry import register_plugin
from sentence_transformers import SentenceTransformer, util
from plugins.localmatcher.localmatcherv2 import run_matching_from_files 
import google.generativeai as genai # NEW: Import genai for type hint

matcher = ProfileMatcher()
@register_plugin("localmatcherv2")
def run(model:SentenceTransformer,job_description_rules:str, # Pass the JD (which is the rules JSON)
            candidate_profile:str,modelgen: genai.GenerativeModel):
    # print(f"📧 localmatcher plugin executed {job_description_rules}")
    # print(f"📧 localmatcher plugin executed {candidate_profile}")
    # matcher = ProfileMatcher()
    # output = matcher.match_fields(model,job_description_rules, candidate_profile)
    output = run_matching_from_files(model, job_description_rules, candidate_profile,modelgen)
    # print(json.dumps(output, indent=2))
    return (output)


# if __name__ == "__main__":
#     with open("req_json_jd.json") as f:
#         req_json = json.load(f)
#     with open("data_json.json") as f:
#         data_json = json.load(f)

#     matcher = ProfileMatcher()
#     output = matcher.match_fields(req_json, data_json)
#     print(json.dumps(output, indent=2))
