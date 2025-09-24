# models/job_description_models.py

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime # <--- ADD THIS IMPORT

class JobDetailsv1(BaseModel):
    job_title: str = Field(..., alias="job_title") # Use alias for job_title
    location: str
    employment_type: str
    about_us: str = Field(..., alias="about_us")
    position_summary: str = Field(..., alias="position_summary")
    key_responsibilities: List[str] = Field(default_factory=list, alias="key_responsibilities")
    required_qualifications: List[str] = Field(default_factory=list, alias="required_qualifications")
    preferred_qualifications: List[str] = Field(default_factory=list, alias="preferred_qualifications")
    what_we_offer: List[str] = Field(default_factory=list, alias="what_we_offer")
    to_apply: str = Field(..., alias="to_apply")
    equal_opportunity_employer_statement: Optional[str] = Field(None, alias="equal_opportunity_employer_statement")
    # jd_embedding_text: Optional[str] = Field(None, alias="jd_embedding_text") # This field is for *internal* embedding text, might not be explicitly in output JSON

    # Model config for aliasing
    model_config = {'populate_by_name': True}

# Top-level model for the JD. The LLM will output this directly.
# models/job_description_models.py

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any

# JobDetails remains unchanged, as user_tags/is_active are top-level JD attributes



from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime # Make sure datetime is imported if using created_at/updated_at

# Define the new nested model for keywordmatch
class KeywordMatchv1(BaseModel):
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class JobDescriptionv1(BaseModel): # Top-level model for the JD. The LLM will output this directly.
    job_title: str 
    location: str
    employment_type: str
    about_us: str
    position_summary: str
    key_responsibilities: List[str]
    required_qualifications: List[str]
    preferred_qualifications: List[str]
    what_we_offer: List[str]
    to_apply: str
    equal_opportunity_employer_statement: Optional[str] = None

    keywordmatch: Optional[KeywordMatchv1] = None # Optional, as it might not always be present

    # NEW: Field for user-defined tags
    user_tags: List[str] = Field(default_factory=list, alias="user_tags") # Expects a list of strings
    # NEW: Field to indicate active status
    is_active: bool = Field(True, alias="is_active") # Default to True
    jd_version: int = Field(1, alias="jd_version") # NEW: Version field, default to 1

    # Fields that will be added by our service after parsing/storage
    embedding: Optional[List[float]] = None
    organization_id: Optional[str] = None
    user_id: Optional[int] = None
    db_id: Optional[Any] = None # Database ID
    created_at: Optional[datetime] = None # New, fetch from DB
    updated_at: Optional[datetime] = None # New, fetch from DB

    model_config = {'populate_by_name': True} # For Pydantic v2