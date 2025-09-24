// src/components/resume_upload/ResumeUploadForm.tsx
import React, { useState ,useEffect} from 'react';
import { Box, Typography, Button, LinearProgress, Alert, Grid, Divider, List, ListItem, ListItemText, Chip, Paper, SelectChangeEvent } from '@mui/material';
import {
  
  Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { Theme, useTheme } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import { uploadResumeApi } from '../../services/apiService';
import { MatchResult } from '../../types/matchTypes';
import {MatchResultResponse} from '../../types/matchTypes'; // adjust path as needed
import MatchResultDialog from '../dialogs/MatchResultDialog';
import TitledCard from '../common/TitledCard';

import axios, { AxiosError } from 'axios';
import { matchProfileToJobApi } from '../../services/apiService';
import { uploadResumeApiv1, getOrganizationsApi, getJobDescriptionsApi } from '../../services/apiService';
import { Organization, JobDescription } from '../../types/jobDescriptionTypes';
// Adjust path based on your actual folder structure for types
import { 
  ParsedResumeData, 
  SkillObject, 
  NestedPeriod,
  ExperienceItem, // << IMPORT
  EducationItem,  // << IMPORT
  CertificationItem, // << IMPORT
  TimeSpentInOrgItem // << IMPORT
  // ProjectItem, // << IMPORT if you render projects
} from '../../types/resumeTypes'; 

// SectionTitle Helper Component
const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Typography variant="h6" component="h3" gutterBottom sx={{ mt: 1.5, mb: 0.5, fontWeight: 'bold', color: 'primary.main', fontSize: '1.1rem' }}>
    {children}
  </Typography>
);




const ResumeUploadForm: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);
  const [parsedData, setParsedData] = useState<ParsedResumeData | null>(null);
  const theme = useTheme();
  const [matchResult, setMatchResult] = useState<{ success: boolean; message: string } | null>(null);
// state
  const [matchDialogOpen, setMatchDialogOpen] = useState(false);
// const [matchResults, setMatchResults] = useState<MatchResult[]>([]);
  const [matchResults, setMatchResults] = useState<MatchResultResponse | null>(null);

  // State for dropdowns and their data
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');

  // Loading and state management
  const [uploading, setUploading] = useState<boolean>(false);
  const [loadingOrgs, setLoadingOrgs] = useState<boolean>(true);
  const [loadingJobs, setLoadingJobs] = useState<boolean>(false);
// on Match click (after getting response)
  const allowedFileTypes = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
  const handleMatch = async () => {
  if (!parsedData?.db_id || !selectedJobId) return;
  try {
    const response = await matchProfileToJobApi(Number(selectedJobId), parsedData.db_id);
    // setMatchResult({ success: true, message: 'Match successful!' });

    setMatchResults(response.data);
    
    console.log('OPening ')
    setMatchDialogOpen(true);

  } catch (error: any) {
    console.error('Match failed:', error);
    setMatchResult({ success: false, message: 'Failed to match resume with job description.' });
  }
};
  
  // Effect to fetch organizations on component mount
  useEffect(() => {
    const fetchOrgs = async () => {
      setLoadingOrgs(true);
      try {
        const response = await getOrganizationsApi();
        setOrganizations(response.data.organizations || []);
      } catch (error) {
        console.error("Failed to fetch organizations", error);
        setMessage({ type: 'error', text: 'Could not load organizations.' });
      } finally {
        setLoadingOrgs(false);
      }
    };
    fetchOrgs();
  }, []); // Runs once on mount

  // Effect to fetch job descriptions when an organization is selected
  useEffect(() => {
    if (!selectedOrgId) {
      setJobDescriptions([]);
      setSelectedJobId('');
      return;
    }

    const fetchJobs = async () => {
      setLoadingJobs(true);
      try {
        const response = await getJobDescriptionsApi(selectedOrgId);
        setJobDescriptions(response.data || []); // The API service already extracts the array
      } catch (error) {
        console.error(`Failed to fetch jobs for org ${selectedOrgId}`, error);
        setMessage({ type: 'error', text: 'Could not load jobs for the selected organization.' });
      } finally {
        setLoadingJobs(false);
      }
    };

    fetchJobs();
  }, [selectedOrgId]); // Re-runs when selectedOrgId changes

  const handleOrgChange = (event: SelectChangeEvent<string>) => {
    setSelectedOrgId(event.target.value);
    setSelectedJobId(''); // Reset job selection when organization changes
  };


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => { /* ... (no change) ... */
    setMessage(null);
    setParsedData(null);
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      if (allowedFileTypes.includes(file.type)) {
        setSelectedFile(file);
      } else {
        setSelectedFile(null);
        setMessage({ type: 'error', text: 'Invalid file type. Please upload a .docx file.' });
      }
    }
  };

  const handleUpload = async () => { /* ... (no change in this logic) ... */
    if (!selectedFile || !selectedOrgId) {
      setMessage({ type: 'info', text: 'Please select an organization and a file to upload.' });
      return;
    }
    setUploading(true);
    setMessage(null);
    setParsedData(null);
    const formData = new FormData();
    formData.append('resume', selectedFile);
    try {
      //const response = await uploadResumeApi(formData);
      const response = await uploadResumeApiv1(formData, selectedOrgId);
      const result: ParsedResumeData = response.data;
      const successMessage = result.db_id ? `Resume for ${result.name || 'candidate'} (ID: ${result.db_id}) parsed!` : 'Resume uploaded and parsed!';
      setMessage({ type: 'success', text: successMessage });
      setParsedData(result);
      setSelectedFile(null);
    } catch (error: any) {
      console.error('Upload error:', error);
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<any>;
        if (axiosError.response) {
          const errorData = axiosError.response.data;
          setMessage({ type: 'error', text: errorData?.error || errorData?.message || 'Upload failed. Server responded with an error.' });
        } else if (axiosError.request) {
          setMessage({ type: 'error', text: 'No response from server during upload. Check network or server status.' });
        } else {
          setMessage({ type: 'error', text: 'Error setting up upload request: ' + axiosError.message });
        }
      } else {
         setMessage({ type: 'error', text: 'An unexpected error occurred during upload.' });
      }
    } finally {
      setUploading(false);
    }
  };

  const renderSkillChips = (skillCategoryName: string, skillsArray?: Array<SkillObject>) => { /* ... (keep as is from previous correct version) ... */
    if (!skillsArray || skillsArray.length === 0) {
      return <Typography variant="body2" color="text.secondary">N/A</Typography>;
    }
    return skillsArray.map((skillItem: SkillObject, index: number) => {
      if (skillItem && typeof skillItem.name === 'string') {
        let chipLabel = skillItem.name;
        if (skillItem.experience_years !== undefined && skillItem.experience_years !== null) {
          chipLabel += ` (${skillItem.experience_years} yr${skillItem.experience_years === 1 ? '' : 's'})`;
        }
        return (
          <Chip 
            key={`${skillCategoryName}-${chipLabel}-${index}`}
            label={chipLabel} 
            sx={{ mr: 0.5, mb: 0.5 }} 
            variant="outlined"
          />
        );
      }
      console.warn(`Skipping skill item in ${skillCategoryName} due to unexpected format or missing name property:`, skillItem);
      return null; 
    }).filter(Boolean);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TitledCard title="📄 Resume Upload & Matching">
        <Grid container spacing={2} alignItems="center">
          {/* Organization Dropdown */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth disabled={loadingOrgs}>
              <InputLabel id="org-select-label">Organization</InputLabel>
              <Select
                labelId="org-select-label"
                value={selectedOrgId}
                label="Organization"
                onChange={handleOrgChange}
              >
                {organizations.map((org) => (
                  <MenuItem key={org.id} value={org.id}>
                    {org.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Job ID Dropdown */}
          <Grid item xs={12} md={3}>
            <FormControl fullWidth disabled={!selectedOrgId || loadingJobs}>
              <InputLabel id="job-id-label">Job ID</InputLabel>
              <Select
                labelId="job-id-label"
                id="job-id-select"
                value={selectedJobId}
                label="Job ID"
                onChange={(e) => setSelectedJobId(e.target.value as string)}
              >
                {jobDescriptions.map((jd) => (
                  <MenuItem key={jd.id} value={jd.id}>
                    {jd.id} - {jd.job_title?.data}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Action Buttons */}
          <Grid item xs={12} md={6} sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              accept=".docx"
              style={{ display: 'none' }}
              id="resume-upload-button"
              type="file"
              onChange={handleFileChange}
              disabled={!selectedOrgId || uploading}
            />
            <label htmlFor="resume-upload-button">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadIcon />}
                disabled={!selectedOrgId || uploading}
              >
                {selectedFile ? 'Change .docx File' : 'Choose .docx File'}
              </Button>
            </label>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!selectedFile || !selectedOrgId || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload & Parse'}
            </Button>
            <Button variant="contained" color="secondary" disabled={!selectedJobId || !parsedData} onClick={handleMatch}>Match</Button>
          </Grid>
        </Grid>

        {selectedFile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, p: 1, border: '1px dashed', borderColor: 'divider', borderRadius: 1 }}>
            <InsertDriveFileIcon color="action" />
            <Typography variant="caption">
              {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
            </Typography>
          </Box>
        )}

        {uploading && <LinearProgress sx={{ mt: 2 }} />}
        {message && (
          <Alert severity={message.type} sx={{ mt: 2 }}>{message.text}</Alert>
        )}
        {matchResult && (
          <Alert severity={matchResult.success ? 'success' : 'error'} sx={{ mt: 2 }}>{matchResult.message}</Alert>
        )}
      </TitledCard>

      {/* Display Parsed Data Section */}
      {parsedData && (
        <TitledCard title={`📝 Parsed Resume Details (ID: ${parsedData.db_id || 'N/A'})`}>
          <Grid container spacing={3}>
            {/* Basic Information & Overview */}
            <Grid item xs={12} md={6}>
              <SectionTitle>👤 Basic Information</SectionTitle>
              <Typography variant="subtitle1" gutterBottom><strong>Name:</strong> {parsedData.name || 'N/A'}</Typography>
              {parsedData.contact?.email && <Typography variant="body2" sx={{mb:0.5}}><strong>Email:</strong> {parsedData.contact.email}</Typography>}
              {parsedData.contact?.phone && <Typography variant="body2" sx={{mb:0.5}}><strong>Phone:</strong> {parsedData.contact.phone}</Typography>}
              {parsedData.contact?.location && <Typography variant="body2" sx={{mb:0.5}}><strong>Location:</strong> {parsedData.contact.location}</Typography>}
              {parsedData.contact?.linkedin && <Typography variant="body2" sx={{mb:0.5}}><strong>LinkedIn:</strong> <a href={parsedData.contact.linkedin} target="_blank" rel="noopener noreferrer">{parsedData.contact.linkedin}</a></Typography>}
              {parsedData.contact?.github && <Typography variant="body2" sx={{mb:0.5}}><strong>GitHub:</strong> <a href={parsedData.contact.github} target="_blank" rel="noopener noreferrer">{parsedData.contact.github}</a></Typography>}
            </Grid>
            <Grid item xs={12} md={6}>
              <SectionTitle>📈 Experience Overview</SectionTitle>
              <Typography variant="body2" gutterBottom><strong>Total Experience:</strong> {parsedData.total_experience_years !== undefined ? `${parsedData.total_experience_years} years` : 'N/A'}</Typography>
              <Typography variant="body2" gutterBottom><strong>Organization Switches:</strong> {parsedData.organization_switches !== undefined ? parsedData.organization_switches : 'N/A'}</Typography>
            </Grid>
            <Grid item xs={12}><SectionTitle>📝 Summary</SectionTitle><Typography variant="body2" sx={{ whiteSpace: 'pre-line', textAlign: 'justify', lineHeight: 1.6 }}>{parsedData.summary || 'N/A'}</Typography></Grid>

            {/* Work Experience - Corrected Typing */}
            {/* {parsedData.experience && parsedData.experience.length > 0 && (
              <Grid item xs={12}>
                <SectionTitle>💼 Work Experience</SectionTitle>
                {parsedData.experience.map((exp: ExperienceItem, index: number) => ( // <<<< EXPLICIT TYPE
                  <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">{exp.title || 'Role N/A'}</Typography>
                    <Typography variant="body1" color="text.primary" gutterBottom>{exp.company || 'Company N/A'}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{mb:1}}>{exp.from || 'Date N/A'} - {exp.to || 'Date N/A'} {exp.location && `| ${exp.location}`}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{whiteSpace: 'pre-line', lineHeight: 1.6}}>{exp.description || 'N/A'}</Typography>

                    
                    {exp.technologies && exp.technologies.map((tech: string, techIndex: number) => ( // <<<< EXPLICIT TYPE
                        <Chip key={techIndex} label={tech} size="small" variant="filled" sx={{bgcolor: 'grey.200', fontWeight:'medium', mr:0.5, mb:0.5}} />
                    ))}
                  </Paper>
                ))}
              </Grid>
            )} */}

{parsedData.experience && parsedData.experience.length > 0 && (
  <Grid item xs={12}>
    <SectionTitle>💼 Work Experience</SectionTitle>
    {parsedData.experience.map((exp: ExperienceItem, index: number) => (
      <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 1 }}>
        <Typography variant="subtitle1" fontWeight="bold">
          {exp.title || 'Role N/A'}
        </Typography>
        <Typography variant="body1" color="text.primary" gutterBottom>
          {exp.company || 'Company N/A'}
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
          {exp.from || 'Date N/A'} - {exp.to || 'Date N/A'} {exp.location && `| ${exp.location}`}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
          {exp.description || 'N/A'}
        </Typography>

        {/* 🧠 Technologies */}
        {exp.technologies && exp.technologies.length > 0 && (
          <Box sx={{ mt: 1, mb: 1 }}>
            {exp.technologies.map((tech: string, techIndex: number) => (
              <Chip
                key={techIndex}
                label={tech}
                variant="filled"
                sx={{ bgcolor: 'grey.200', fontWeight: 'medium', mr: 0.5, mb: 0.5 }}
              />
            ))}
          </Box>
        )}

        {/* ✅ Nested Assignments / Projects */}
        {Array.isArray(exp.nested_periods) && exp.nested_periods.length > 0 && (
          <Box sx={{ mt: 2, ml: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'medium', mb: 1 }}>
              🧩 Assignments / Projects:
            </Typography>
            {exp.nested_periods.map((period: NestedPeriod, nestedIndex: number) => (
              <Paper
                key={nestedIndex}
                variant="outlined"
                sx={{ p: 1.5, mb: 1.5, backgroundColor: '#f9f9f9' }}
              >
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}
                >
                  {period.description || 'No Description'}
                </Typography>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  display="block"
                  sx={{ mt: 0.5 }}
                >
                  {period.from || 'N/A'} - {period.to || 'N/A'}
                </Typography>
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    ))}
  </Grid>
)}


            {/* Skills Section - No change needed here if renderSkillChips is correct */}
            {parsedData.skills && ( <Grid item xs={12}> <SectionTitle>🛠️ Skills</SectionTitle>
                {Object.entries(parsedData.skills).map(([category, skillsList]) => (
                  Array.isArray(skillsList) && skillsList.length > 0 && (
                    <Box key={category} sx={{ mb: 1.5 }}>
                      <Typography variant="subtitle2" sx={{ textTransform: 'capitalize', fontWeight: 500, mb: 0.5 }}>{category.replace(/_/g, ' ')}:</Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {renderSkillChips(category, skillsList as Array<SkillObject>)}
                      </Box>
                    </Box>
                  )
                ))}
              </Grid>
            )}

            {/* Education - Corrected Typing */}
            {parsedData.education && parsedData.education.length > 0 && (
              <Grid item xs={12} md={6}>
                <SectionTitle>🎓 Education</SectionTitle>
                <List dense disablePadding>
                  {parsedData.education.map((edu: EducationItem, index: number) => ( // <<<< EXPLICIT TYPE
                    <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                      <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={`${edu.degree || 'Degree N/A'}${edu.field_of_study ? ` in ${edu.field_of_study}` : ''}`} secondary={`${edu.institution || 'Institution N/A'} ${edu.dates ? `(${edu.dates})` : ''}`} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}

            {/* Certifications - Corrected Typing */}
            {parsedData.certifications && parsedData.certifications.length > 0 && (
              <Grid item xs={12} md={6}>
                <SectionTitle>📜 Certifications</SectionTitle>
                <List dense disablePadding>
                  {parsedData.certifications.map((cert: CertificationItem, index: number) => ( // <<<< EXPLICIT TYPE
                    <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                      <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={cert.name || 'Unnamed Certification'} secondary={`${cert.issuing_organization || 'N/A'} ${cert.date ? `(${cert.date})` : ''}`} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}
            
            {/* Technology Experience Years */}
            {parsedData.technology_experience_years && Object.keys(parsedData.technology_experience_years).length > 0 && (
                <Grid item xs={12}> <SectionTitle>💡 Technology Experience (Years)</SectionTitle>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {Object.entries(parsedData.technology_experience_years).map(([tech, years]: [string, number], index: number) => ( // <<<< EXPLICIT TYPE
                            <Chip key={index} label={`${tech}: ${years} yrs`} variant="filled" sx={{bgcolor: 'grey.300', fontWeight:'medium'}} />
                        ))}
                    </Box>
                </Grid>
            )}

            {/* Time Spent In Organizations - Corrected Typing */}
            {parsedData.time_spent_in_org && parsedData.time_spent_in_org.length > 0 && (
                <Grid item xs={12}> <SectionTitle>🏢 Time Spent In Organizations</SectionTitle>
                    <List dense disablePadding>
                        {parsedData.time_spent_in_org.map((org_time: TimeSpentInOrgItem, index: number) => ( // <<<< EXPLICIT TYPE
                            <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5}}>
                                <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={org_time.company_name || "N/A"} secondary={`Years: ${org_time.total_duration_years?.toFixed(1) || 'N/A'}, Months: ${org_time.total_duration_months?.toFixed(1) || 'N/A'}`} />
                            </ListItem>
                        ))}
                    </List>
                </Grid>
            )}

{parsedData.current_company && (
  <Grid item xs={12}>
    <SectionTitle>💼 Current Role</SectionTitle>
    <Typography variant="body2"><strong>Company:</strong> {parsedData.current_company}</Typography>
    <Typography variant="body2"><strong>Title:</strong> {parsedData.current_title || 'N/A'}</Typography>
    <Typography variant="body2"><strong>Tenure:</strong> {parsedData.current_tenure_years?.toFixed(2) || 'N/A'} years</Typography>
  </Grid>
)}

{parsedData.recent_skills_overview && (
  <Grid item xs={12}>
    <SectionTitle>🧠 Recent Skills Overview</SectionTitle>
    {Object.entries(parsedData.recent_skills_overview).map(([category, skillsList]) => (
      Array.isArray(skillsList) && skillsList.length > 0 && (
        <Box key={category} sx={{ mb: 1.5 }}>
          <Typography variant="subtitle2" sx={{ textTransform: 'capitalize', fontWeight: 500, mb: 0.5 }}>
            {category.replace(/_/g, ' ')}:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {skillsList.map((skill: any, index: number) => (
              <Chip
                key={`${category}-${skill.name}-${index}`}
                label={`${skill.name} (${skill.experience_years} yrs)`}
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      )
    ))}
  </Grid>
)}


            {parsedData.achievements && parsedData.achievements.length > 0 && (
              <Grid item xs={12}>
                <SectionTitle>🏆 Achievements</SectionTitle>
                <List dense>
                  {parsedData.achievements.map((achievement, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={achievement} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}

          </Grid>
        </TitledCard>
        
      )}

{matchDialogOpen && matchResults && (
<MatchResultDialog
  open={matchDialogOpen}
  matchResponse={matchResults}  // ✅ Correct prop name
  onClose={() => setMatchDialogOpen(false)}
/>
)}
    </Box>
  );
};



export default ResumeUploadForm;