// src/services/apiService.ts

// src/services/apiService.ts
import axios, { AxiosResponse, AxiosError } from 'axios'; // Import Axios types
// import { LoginResponseData } from '../types/authTypes'; // <<<<< NEW IMPORT

import { Organization, JobDescription } from '../types/jobDescriptionTypes'; // <<<<< NEW IMPORT
import { MatchResultApiResponse } from '../types/matchTypes';
import { CreateUserPayload, User } from '../types/userTypes';
import { LoginResponseData, RegisterPayload } from '../types/authTypes';

// --- NEW INTERFACE FOR ACTIVE JOB DESCRIPTION COUNT API RESPONSE ---
export interface ActiveJobDescriptionCountResponse {
  organizationId: string;
  activeJobDescriptionCount: number;
}

// --- NEW INTERFACE FOR PROFILE COUNT API RESPONSE ---
export interface ProfileCountResponse {
  organizationId: string;
  profileCount: number;
}

// --- User Management Service Functions ---

/**
 * Creates a new user in the system.
 * @param userData The data for the new user.
 * @returns Promise<AxiosResponse<User>>
 */
export async function createUserApi(userData: CreateUserPayload): Promise<AxiosResponse<User>> {
  return apiClient.post('/users/create', userData);
}

export async function registerApi(payload: RegisterPayload): Promise<AxiosResponse> {
  return apiClient.post('/auth/register/new', payload);
}
// --- NEW INTERFACE FOR GET_JOB_DESCRIPTIONS_API RESPONSE ---
interface GetJobDescriptionsApiResponse {
  jobDescriptions: JobDescription[]; // The array of JDs is nested under 'jobDescriptions' key
}

// --- NEW INTERFACE FOR GET_ORGANIZATIONS_API RESPONSE ---
interface GetOrganizationsApiResponse {
  organizations: Organization[]; // The array is nested under 'organizations' key
}

// --- NEW INTERFACES FOR BULK UPLOAD LIST ---
export interface BulkUploadHistoryItem {
  upload_id: string;
  filename: string;
  status: string; // e.g., 'completed', 'processing', 'failed'
  created_at: string;
  updated_at: string | null;
}

export interface GetBulkUploadListApiResponse {
  upload_history: BulkUploadHistoryItem[];
}


// const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000/api';
//PRODUCTION
// const API_BASE_URL = 'https://api.hyreassist.co/api';

//DEVELOPMENT
const API_BASE_URL = '/api'; // <<<<< CHANGE THIS TO A RELATIVE PATH

// Create an axios instance with default configurations
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // <<<<<< CRITICAL: This tells axios to send cookies
});

// Optional: Axios interceptors for global request/response logging or error handling
apiClient.interceptors.request.use(
  (config) => {
    // You can modify request config here if needed
    console.log('Axios Request as:', config.method?.toUpperCase(), config.url, config.data || config.params);
    return config;
  },
  (error) => {
    console.error('Axios Request Error:', error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    console.log('Axios Response:', response.status, response.data);
    return response;
  },
  (error: AxiosError) => {
    // Handle global errors or just log them
    if (error.response) {
      console.error('Axios Error Response Status:', error.response.status);
      console.error('Axios Error Response Data:', error.response.data);
    } else if (error.request) {
      console.error('Axios Error Request (no response received):', error.request);
    } else {
      console.error('Axios Error Message:', error.message);
    }
    return Promise.reject(error); // Important to re-reject so calling code can catch it
  }
);


// --- Authentication Service Functions ---

/**
 * Calls the backend login endpoint.
 * Returns the AxiosResponse object (data will be in response.data).
 * Axios throws an error for non-2xx status codes.
 */
// export async function loginUserApi(organizationId: string, firebaseIdToken: string): Promise<AxiosResponse> {
//   return apiClient.post('/auth/login', { // Path is relative to baseURL
//     organizationId,
//     firebaseIdToken,
//   });
// }

// <<<<< UPDATED: Returns Promise<AxiosResponse<LoginResponseData>> >>>>>
export async function loginUserApi(organizationId: string, firebaseIdToken: string): Promise<AxiosResponse<LoginResponseData>> {
  return apiClient.post('/auth/login', { organizationId, firebaseIdToken });
}

/**
 * Calls the backend to check the current authentication status.
 * Returns the AxiosResponse object.
 */
// export async function checkAuthStatusApi(): Promise<AxiosResponse> {
//   return apiClient.get('/auth/status');
// }

// <<<<< UPDATED: Returns Promise<AxiosResponse<LoginResponseData>> >>>>>
export async function checkAuthStatusApi(): Promise<AxiosResponse<LoginResponseData>> {
  return apiClient.get('/auth/status');
}

/**
 * Calls the backend registration finalization endpoint.
 */
export async function registerUserApi(
  organizationId: string,
  firebaseIdToken: string,
  fullName?: string
): Promise<AxiosResponse> {
  return apiClient.post('/auth/register', {
    organizationId,
    firebaseIdToken,
    fullName,
  });
}

// --- Resume Upload Service Function ---
/**
 * Uploads a resume file to the backend using FormData.
 * @param formData FormData object containing the resume file
 * @returns Promise<AxiosResponse>
 */
export async function uploadResumeApi(formData: FormData): Promise<AxiosResponse> {
  // For FormData, axios automatically sets the 'Content-Type' to 'multipart/form-data'
  // along with the correct boundary.
  return apiClient.post('/profile/upload-resume', formData, {
    // Optional: If you need to listen to upload progress, axios has onUploadProgress config
    // onUploadProgress: progressEvent => {
    //   if (progressEvent.total) {
    //     const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
    //     console.log(`Upload Progress: ${percentCompleted}%`);
    //   }
    // }
  });
}

// --- NEW GENERIC FILE UPLOAD FUNCTION ---
// This function takes the specific endpoint as its first argument.
export async function uploadFileApi(endpoint: string, formData: FormData): Promise<AxiosResponse> {
  return apiClient.post(endpoint, formData, {
    headers: { 'X-Custom-Upload-Request': 'true' } // Ensure this header is still needed for preflight
  });
}

// --- NEW Resume Analysis Upload Service Function (for /v2/upload_resume) ---
export async function uploadResumeV2Api(formData: FormData): Promise<AxiosResponse> {
  return apiClient.post('/profile/v2/upload_resume', formData, {
    headers: { 'X-Custom-Upload-Request': 'true' } // Assuming this endpoint also needs preflight
  });
}


// API VISIONING

/**
 * Uploads a resume file to the backend using FormData.
 * @param formData FormData object containing the resume file
 * @returns Promise<AxiosResponse>
 */
export async function uploadResumeApiv1(formData: FormData, organizationId: string): Promise<AxiosResponse> {
  // For FormData, axios automatically sets the 'Content-Type' to 'multipart/form-data'
  // along with the correct boundary.
  const url = `/profile/v1/upload_resume?organization_id=${organizationId}`;
  return apiClient.post(url, formData, {});
}
export async function uploadResumeApiv3(formData: FormData): Promise<AxiosResponse> {
  return apiClient.post('/profile/v3/upload_resume', formData, {
    headers: { 'X-Custom-Upload-Request': 'true' } // Assuming this endpoint also needs preflight
  });
}
// /api/jd/v1/upload_jd

// --- NEW Job Description Service Functions ---

// --- Corrected getOrganizationsApi ---
/**
 * Fetches a list of organizations the logged-in user has access to.
 * Now expects the response.data to be an object { organizations: Organization[] }.
 * @returns Promise<AxiosResponse<GetOrganizationsApiResponse>>
 */
export async function getOrganizationsApi(): Promise<AxiosResponse<GetOrganizationsApiResponse>> {
  // Update this endpoint path if it's different in your backend
  return apiClient.get('/organization/v1/accessible_list'); 
}

/**
 * Fetches the count of active job descriptions for the user's organization.
 * @returns Promise<AxiosResponse<ActiveJobDescriptionCountResponse>>
 */
export async function getActiveJobDescriptionCountApi(): Promise<AxiosResponse<ActiveJobDescriptionCountResponse>> {
  return apiClient.get('/jd/v1/active_count');
}

/**
 * Fetches the count of active profiles for the user's organization.
 * @returns Promise<AxiosResponse<ProfileCountResponse>>
 */
export async function getActiveProfileCountApi(): Promise<AxiosResponse<ProfileCountResponse>> {
  // The user's organization context is handled by the backend session.
  return apiClient.get('/profile/v1/profile_count');
}

export const matchProfileToJobApi = (jobId: number, profileId: number) => {
  return axios.post('/api/match/v1/match', {
    jobId,
    profileId
  });
};

// apiService.ts



// export const getCandidateMatchesApi = async (organization_id: number, job_id: number): Promise<MatchResultApiResponse> => {
//   const response = await axios.get<MatchResultApiResponse>('/api/match/v1/search');
//   return response.data;
// };




export const getCandidateMatchesApi = async (
  organization_id: string,
  job_id: string,
  upload_id?: string
): Promise<MatchResultApiResponse> => {
    const params: any = { organization_id, job_id };
    if (upload_id) {
      params.upload_id = upload_id;
    }
    const response = await axios.get<MatchResultApiResponse>('/api/match/v1/search', {
      params,
    });
    return response.data;
  };

/**
 * Uploads a job description file.
 * @param organizationId The ID of the organization for which the JD is uploaded.
 * @param formData FormData containing the JD file (field name 'job_description')
 * @returns Promise<AxiosResponse<JobDescription>> Returns the created JobDescription object on success.
 */
export async function uploadJobDescriptionApi(organizationId: string, formData: FormData): Promise<AxiosResponse<JobDescription>> {
  // Pass organization_id as a query param or hidden field in FormData if backend expects it
  // For simplicity, let's assume backend gets it from form data or from user's session token.
  // If backend expects org_id in form, ensure formData.append('organization_id', organizationId);
  
  return apiClient.post(`/jd/v1/upload_jd?organization_id=${organizationId}`, formData, { // Assuming query param for orgId
    headers: { 'X-Custom-Upload-Request': 'true' } // Ensure preflight
  });
}
//@jd_bp.route('/jd/v1/list_by_organization/<string:organization_id>', methods=['GET'])

/**
 * Uploads a job description file.
 * @param organizationId The ID of the organization for which the JD is uploaded.
 * @param formData FormData containing the JD file (field name 'job_description')
 * @returns Promise<AxiosResponse<JobDescription>> Returns the created JobDescription object on success.
 */
export async function uploadJobDoc(organizationId: string, formData: FormData): Promise<AxiosResponse<JobDescription>> {
  // Pass organization_id as a query param or hidden field in FormData if backend expects it
  // For simplicity, let's assume backend gets it from form data or from user's session token.
  // If backend expects org_id in form, ensure formData.append('organization_id', organizationId);
  return apiClient.post(`/v1/upload_jd?organization_id=${organizationId}`, formData, { // Assuming query param for orgId
    headers: { 'X-Custom-Upload-Request': 'true' } // Ensure preflight
  });
}
///v1/upload_jd
/**
 * Fetches a list of job descriptions for a specific organization.
 * @param organizationId The ID of the organization.
 * @returns Promise<AxiosResponse<JobDescription[]>>
 */
// export async function getJobDescriptionsApi(organizationId: string): Promise<AxiosResponse<JobDescription[]>> {
//   return apiClient.get(`/v1/job-descriptions?organization_id=${organizationId}`); // Assuming query param
// }


/**
 * NEW/Corrected: Fetches a list of job descriptions for a specific organization.
 * Now uses the new endpoint and extracts the array from 'jobDescriptions' key.
 * @param organizationId The ID of the organization.
 * @returns Promise<AxiosResponse<JobDescription[]>>
 */
export async function getJobDescriptionsApi(organizationId: string): Promise<AxiosResponse<JobDescription[]>> {
  // Use the new endpoint path
  const response: AxiosResponse<GetJobDescriptionsApiResponse> = await apiClient.get(`/jd/v1/list_by_organization/${organizationId}`);
  // Extract the array from the 'jobDescriptions' key
  return { ...response, data: response.data.jobDescriptions }; // Return AxiosResponse-like object with corrected data
}

// apiService.ts
export async function semanticSearchJobDescriptionsApi(query: string): Promise<AxiosResponse<JobDescription[]>> {
  const response = await apiClient.get(`/jd/v1/semantic_search_jd`, {
    params: { query }
  });
  return { ...response, data: response.data.jobDescriptions };
}

export async function getJobRuleByIdApi(jobId: string) {
  return apiClient.get(`/jd/v1/rule/${jobId}`);
}

/**
 * Uploads a zip file of resumes for bulk processing.
 * @param organizationId The ID of the organization.
 * @param jobId The ID of the job to associate the resumes with.
 * @param zipFile The zip file to upload.
 * @returns Promise<AxiosResponse> The backend should return a list of files being processed.
 */
// export async function bulkUploadResumesApi(organizationId: string, jobId: string, zipFile: File): Promise<AxiosResponse> {
//   const formData = new FormData();
//   formData.append('zip_file', zipFile);
//   formData.append('organization_id', organizationId);
//   formData.append('job_id', jobId);
// console.debug('DATA ',organizationId);
// console.debug('DATA ',jobId);
// console.debug('DATA ',zipFile);
//   return apiClient.post('/profile/v1/bulk_upload_resume', formData,  {
//     headers: { 'X-Custom-Upload-Request': 'true' } // Assuming this endpoint also needs preflight
//   });
// }

export async function bulkUploadResumesApi(organizationId: string, jobId: string, zipFile: File, fileName: string): Promise<AxiosResponse> {
  const formData = new FormData();
  formData.append('zip_file', zipFile); // zipFile remains in formData

  // Append organizationId, jobId, and fileName as query parameters to the URL
  const url = `/profile/v1/bulk_upload_resume?organization_id=${organizationId}&job_id=${jobId}&file_name=${encodeURIComponent(fileName)}`;

  return apiClient.post(url, formData,  { // Pass the constructed URL
    headers: { 'X-Custom-Upload-Request': 'true' }
  });
}

/**
 * Fetches the bulk upload history for a given organization and job.
 * @param organizationId The ID of the organization.
 * @param jobId The ID of the job.
 * @param startDate Optional start date in 'YYYY-MM-DD' format.
 * @param endDate Optional end date in 'YYYY-MM-DD' format.
 * @returns Promise<AxiosResponse<GetBulkUploadListApiResponse>>
 */
export async function getBulkUploadListApi(
  organizationId: string, 
  jobId: string,
  startDate?: string,
  endDate?: string
): Promise<AxiosResponse<GetBulkUploadListApiResponse>> {
  const params: any = {
    organization_id: organizationId,
    job_id: jobId,
  };

  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  // The endpoint path might need adjustment, e.g., to /profile/v1/bulk_upload_list
  return apiClient.get('/profile/v1/bulk_upload_list', { params });
}

/**
 * Generates a URL to view a specific job description document.
 * This is frontend logic; the backend will generate the actual file serving URL.
 * @param jobDescId The ID of the job description.
 * @returns string The full URL to view the document.
 */
export function getJobDescriptionViewUrl(jobDescId: string): string {
  // The backend endpoint will be /api/job-descriptions/view/<id>
  // axios.defaults.baseURL already has /api
  return `${API_BASE_URL}/v1/job-descriptions/view/${jobDescId}`; 
}



// export const getJobDescriptionsApi = async (organizationId: string) => {
//   return [
//     { id: 'JOB001' },
//     { id: 'JOB002' },
//     { id: 'JOB003' },
//   ]; // Replace with actual API
// };

export const getJobDescriptionDetailsApi = async (jobId: string) => {
  return {
    description: `Description for ${jobId}`,
  };
};

export const mockCandidateSearchApi = async ({ jobId, jobDescription }: any) => {
  return [
    { profileId: 'PROF001', candidateName: 'Alice', matchScore: 87 },
    { profileId: 'PROF002', candidateName: 'Bob', matchScore: 74 },
  ];
};
