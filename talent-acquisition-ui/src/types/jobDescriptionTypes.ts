// src/types/jobDescriptionTypes.ts

export interface Organization {
  id: string;
  name: string;
}

export interface JobDescription {
  id: string;
  // organization_id: string;
  organization_id: { data: string };

  file_name: string;
  description_snippet?: string;
  uploaded_at: string;
  // job_title?: string; // Add if your backend returns this
  job_title?: { data: string };
  location?: string;
  employment_type?: string;
  about_us?: string;
  // position_summary?: string;
  position_summary?: { data: string };

  key_responsibilities?: string[];
  required_qualifications?: string[];
  preferred_qualifications?: string[];
  what_we_offer?: string[];
  to_apply?: string;
  equal_opportunity_employer_statement?: string | null;
  userId?: number;
  created_at?: string;
}

// --- NEW: Props interface for the DocxUploadModal component ---
// export interface DocxUploadModalProps {
//   open: boolean;
//   onClose: () => void;
//   onUpload: (file: File, orgId: string) => Promise<void>;
//   currentOrgId: string;
// }