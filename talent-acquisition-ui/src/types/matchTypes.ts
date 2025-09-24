// src/types/matchTypes.ts

export interface SourceEvaluated {
  source_field: string;
  data: any;
  score: number;
  confidence: number;
}

export interface MatchResult {
  field: string;
  score: number;
  confidence: number;
  best_source_used: string;
  req_data: string | string[];
  sources_evaluated: SourceEvaluated[];
}

export interface MatchResultResponse {
  results: MatchResult[];
  overall_score_weighted: number;
  overall_score_average_all: number;
  overall_score_average_non_zero: number;
  max_score: number;
  max_score_field: string;
}

export interface CandidateMatchResult {
  profileId: string;
  candidateName: string;
  matchScore: number;
  totalExperience: number;
  skills: string[];
}




// matchTypes.ts

export interface MatchScorePeriod {
  from: string;
  to: string;
}

export interface MatchSkill {
  name: string;
  experience_years: number;
  periods: MatchScorePeriod[];
}

export interface MatchedDetails {
  jobTitle: string;
  candidateName: string;
  summaryMatch: string;
  recentSkillsFound: {
    languages?: MatchSkill[];
    frameworks?: MatchSkill[];
    [key: string]: MatchSkill[] | undefined;
  };
}

export interface MatchFieldResult {
  status: string;
  score: number;
  matched_data?: string[];
  details?: string;
}

export interface MatchResultsJson {
  job_title_match?: MatchFieldResult;
  location_match?: MatchFieldResult;
  required_qualifications_match?: MatchFieldResult;
  overall_score: number;
  matched_details: MatchedDetails;
}

// export interface MatchResultRecord {
//   id: string;
//   jobId: number;
//   profileId: number;
//   candidateName: string;
//   overallScore: number;
//   matchResultsJson: MatchResultsJson;
//   organizationId: string;
//   agencyId: string | null;
//   createdBy: string;
//   createdAt: string;
// }

export interface MatchResultApiResponse {
  matchResults: MatchResultRecord[];
}

export interface MatchResultRecord {
  id: string;
  jobId: number;
  profileId: number;
  candidateName: string;
  overallScore: number;
  matchResultsJson: any; // You can optionally define this more strictly
  organizationId: string;
  agencyId: string | null;
  createdBy: string;
  createdAt: string;
}
