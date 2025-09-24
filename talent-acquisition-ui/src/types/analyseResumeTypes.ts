// src/types/analyseResumeTypes.ts

export interface SkillObject {
  name: string;
  experience_years?: number | null;
}

export interface ContactInfo { // <<<<< ENSURE THIS INTERFACE IS DEFINED AND USED
  email?: string;
  phone?: string;
  linkedin?: string | null;
  github?: string | null;
  website?: string | null;
  location?: string;
}

export interface WorkExperienceItem {
  role?: string | null;
  company?: string;
  location?: string | null;
  from?: string;
  to?: string;
  description?: string;
  technologies?: string[];
  start_date?: string;
  end_date?: string;
  information?: string;
}


export interface OrganizationDetails {
  role?: string | null;
  company?: string;
  location?: string | null;
  from?: string;
  to?: string;
}

// Interface for the object that CONTAINS work_experiences
export interface WorkExperiencesContainer {
  work_experiences?: WorkExperienceItem[];
}

// Interface for the metadata object within project_experience array
export interface ProjectExperienceMetadata {
  source?: string;
  extractor?: string;
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
}


export interface EducationItem {
  degree?: string;
  end_date?: string;
  location?: string | null;
  start_date?: string;
  institution?: string;
  field_of_study?: string | null;
  dates?: string;
}

export interface CertificationItem {
  name?: string;
  issuing_organization?: string | null;
  date?: string;
}

export interface KeywordMatchDetail {
  weight?: number;
  keyword?: string;
  match_type?: string;
  matched_form_in_text?: string;
}

export interface MissingDetail {
  weight?: number;
  keyword?: string;
}

export interface KeywordMatcher {
  category_scores?: Record<string, number>;
  matched_details?: Record<string, KeywordMatchDetail[]>;
  missing_details?: Record<string, MissingDetail[]>;
  matched_keywords?: string[];
  missing_keywords?: string[];
  overall_match_score?: number;
  total_achieved_score?: number;
  total_possible_score?: number;
}

export interface ProjectExperiencePlugin {
  work_experiences?: WorkExperienceItem[];
  source?: string;
  extractor?: string;
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
}


export interface PluginData {
  keyword_matcher?: KeywordMatcher;
  // project_experience is an array that contains either a WorkExperiencesContainer OR ProjectExperienceMetadata
  project_experience?: Array<WorkExperiencesContainer | ProjectExperienceMetadata>;
}

// NEW: Interface for the simplified work_experiences in the root JSON
export interface OrganizationExperienceSummary {
  role?: string;
  company?: string;
  end_date?: string;
  location?: string | null;
  start_date?: string;
}

export interface TimeSpentInOrgItem {
  company_name?: string;
  total_duration_years?: number;
  total_duration_months?: number;
}

// Main ParsedResumeData interface matching your latest JSON
export interface ParsedResumeData {
  YoE?: string;
  name?: string;
  email?: string;
  contact_number?: string;
  summary?: string;
  skills?: string[];
  embedding?: null;
  file_name?: string;
  educations?: Array<EducationItem>;
  certifications?: Array<CertificationItem>; 
  plugin_data?: PluginData; 

  organization_switches?: number;
  technology_experience_years?: Record<string, number>;
  time_spent_in_org?: Array<TimeSpentInOrgItem>;
  
  db_id?: number;
  contact?: ContactInfo; // <<<<<<<<<<<<<<<<< ADDED THIS LINE
  work_experiences?: OrganizationExperienceSummary[]; // THIS IS THE FIELD WE WILL RENDER
  organizations?: OrganizationExperienceSummary[]; // <<<<<<<<<<<<< ADDED THIS FOR THE NEW SECTION

}

