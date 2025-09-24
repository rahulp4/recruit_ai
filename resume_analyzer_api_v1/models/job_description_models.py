# models/job_description_models.py

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Literal, Union, Any
from datetime import datetime

# --- Reusable Components for Rule Definitions ---
class BaseRuleConfig(BaseModel):
    type: Literal["str", "num"] = Field(..., description="Data type of the field being matched (string or numeric).")
    weightage: int = Field(..., ge=0, le=5, description="Importance weight of this rule (0-5, 5 is highest).")
    matchreq: Literal["jaccard", "vector", "operator"] = Field(..., description="Matching requirement type (Jaccard similarity, Vector similarity, or Operator for numeric/date).")
    profiledatasource: List[str] = Field(default_factory=list, description="Paths in candidate profile JSON to check (e.g., 'experience.title', 'summary').")
    fromsource: Optional[str] = Field(None, description="The original section/field name in the JD text from which this rule's data was extracted (e.g., 'Job Title', 'Position Summary', 'About Us').") # NEW FIELD

    sourcecondition: Optional[Literal["AND", "OR"]] = None 

# --- Specific Rule Models ---

class JobTitleRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list, description="Extracted keywords/phrases for the job title from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"

class LocationRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list, description="Extracted locations from the JD.")
    sourcecondition: Literal["AND", "OR"] = "OR" 
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"

class EmploymentTypeRule(BaseRuleConfig): 
    # CRITICAL FIX: Change data type from str to List[str]
    data: List[str] = Field(default_factory=list, description="Extracted exact employment type(s).") 
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["employment_type"] 

class AboutUsRule(BaseRuleConfig): 
    data: str = Field(..., description="Extracted full text of the 'About Us' statement from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["vector"] = "vector"
    profiledatasource: List[str] = ["summary"]

class PositionSummaryRule(BaseRuleConfig):
    data: str = Field(..., description="Extracted full text of the position summary from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["vector"] = "vector"
    profiledatasource: List[str] = ["experience.description", "summary", "experience.technologies"]

class KeyResponsibilitiesRule(BaseRuleConfig):
    data: str = Field(..., description="Extracted full text of key responsibilities from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["vector"] = "vector"
    profiledatasource: List[str] = ["experience.description", "summary"]

class RequiredQualificationsRule(BaseRuleConfig):
    data: str = Field(..., description="Extracted full text of required qualifications from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["vector"] = "vector"
    profiledatasource: List[str] = ["experience.description", "summary", "skills.languages.name", "skills.frameworks.name", "skills.tools.name", "skills.platforms.name", "certifications.name"]

class PreferredQualificationsRule(BaseRuleConfig):
    data: str = Field(..., description="Extracted full text of preferred qualifications from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["vector"] = "vector"
    profiledatasource: List[str] = ["experience.description", "summary", "skills.languages.name", "skills.frameworks.name", "skills.tools.name", "skills.platforms.name", "certifications.name"]

class DegreeRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list, description="Extracted degree types from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["education.degree", "education.field_of_study"]
    sourcecondition: Literal["AND", "OR"] = "OR"

class FieldOfStudyRule(BaseRuleConfig):
    data: str = Field(..., description="Extracted field of study from the JD.")
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["education.field_of_study"]

class OrganizationSwitchesRule(BaseRuleConfig):
    data: str = Field(..., description="Operator for number of switches (e.g., '<3', '>5', '=2').")
    type: Literal["num"] = "num"
    matchreq: Literal["operator"] = "operator"
    profiledatasource: List[str] = ["organization_switches"]

class CurrentTitleRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list, description="Extracted keywords/phrases for the desired current job title.")
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["current_title"]
# NEW: Specific Rule Models for KeywordMatch categories
class TechnicalSkillsRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list) # Data is a list of strings
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard" # Common for skill lists
    profiledatasource: List[str] = ["skills.languages.name", "skills.frameworks.name", "skills.tools.name", "skills.platforms.name", "experience.technologies"]

class SoftSkillsRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list)
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["summary", "experience.description"]

class CertificationsRule(BaseRuleConfig):
    data: List[str] = Field(default_factory=list)
    type: Literal["str"] = "str"
    matchreq: Literal["jaccard", "vector"] = "jaccard"
    profiledatasource: List[str] = ["certifications.name"]

# NEW: KeywordMatch container model
class KeywordMatch(BaseModel):
    technical_skills: Optional[TechnicalSkillsRule] = None
    soft_skills: Optional[SoftSkillsRule] = None
    certifications: Optional[CertificationsRule] = None

# --- Top-Level Job Matching Rules Model (This is the new main JD model) ---
class JobDescription(BaseModel): 
    job_title: Optional[JobTitleRule] = None
    location: Optional[LocationRule] = None
    employment_type: Optional[EmploymentTypeRule] = None 
    about_us: Optional[AboutUsRule] = None 
    position_summary: Optional[PositionSummaryRule] = None
    key_responsibilities: Optional[KeyResponsibilitiesRule] = None
    required_qualifications: Optional[RequiredQualificationsRule] = None
    preferred_qualifications: Optional[PreferredQualificationsRule] = None
    degree: Optional[DegreeRule] = None
    field_of_study: Optional[FieldOfStudyRule] = None
    organization_switches: Optional[OrganizationSwitchesRule] = None
    current_title: Optional[CurrentTitleRule] = None

    keywordmatch: Optional[KeywordMatch] = None # Optional, as it might not always be present

    user_tags: List[str] = Field(default_factory=list)
    is_active: bool = True
    jd_version: int = 1

    embedding: Optional[List[float]] = None
    organization_id: Optional[str] = None
    user_id: Optional[int] = None
    db_id: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {'populate_by_name': True}