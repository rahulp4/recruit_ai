// src/types/resumeTypes.ts

export interface SkillObject {
  name: string;
  experience_years?: number | null;
}

export interface ExperienceItem { // For items in the 'experience' array
  title?: string | null;
  company?: string;
  location?: string | null;
  from?: string;
  to?: string;
  description?: string;
  technologies?: string[];
  nested_periods?: NestedPeriod[]; // ✅ add this line

}

export interface NestedPeriod {
  description?: string;
  from?: string;
  to?: string;
}

export interface ProjectItem { // For items in the 'projects' array
  name?: string;
  description?: string;
  technologies?: string[];
}

export interface EducationItem { // For items in the 'education' array
  degree?: string;
  field_of_study?: string | null;
  institution?: string | null;
  location?: string | null;
  dates?: string;
}

export interface CertificationItem { // For items in the 'certifications' array
  name?: string;
  issuing_organization?: string | null;
  date?: string;
}

export interface TimeSpentInOrgItem { // For items in 'time_spent_in_org'
  company_name?: string;
  total_duration_years?: number;
  total_duration_months?: number;
}

export interface ParsedResumeData {
    current_company?: string;
  current_title?: string;
  current_tenure_years?: number;
  recent_skills_overview?: { name: string; confidence: number }[];
  achievements?: string[];
  name?: string;
  summary?: string;
  total_experience_years?: number;
  contact?: {
    email?: string;
    phone?: string;
    linkedin?: string | null;
    github?: string | null;
    website?: string | null;
    location?: string;
  };
  experience?: Array<ExperienceItem>; // Use defined type
  skills?: {
    languages?: Array<SkillObject>;
    frameworks?: Array<SkillObject>;
    databases?: Array<SkillObject>;
    tools?: Array<SkillObject>;
    platforms?: Array<SkillObject>;
    methodologies?: Array<SkillObject>;
    other?: Array<SkillObject>;
  };
  projects?: Array<ProjectItem>; // Use defined type (your JSON had empty projects, adjust if needed)
  education?: Array<EducationItem>; // Use defined type
  certifications?: Array<CertificationItem>; // Use defined type
  organization_switches?: number;
  technology_experience_years?: Record<string, number>;
  time_spent_in_org?: Array<TimeSpentInOrgItem>; // Use defined type
  db_id?: number;
}