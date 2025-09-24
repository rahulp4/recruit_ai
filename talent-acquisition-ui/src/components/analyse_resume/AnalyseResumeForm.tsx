// src/components/analyse_resume/AnalyseResumeForm.tsx
import React, { useState } from 'react';
import { Box, Typography, Button, Card, CardContent, LinearProgress, Alert, AlertTitle, Paper, Grid, Divider, List, ListItem, ListItemText, Chip } from '@mui/material';
import { Theme, useTheme } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import { uploadResumeV2Api } from '../../services/apiService';
import { uploadResumeApiv3 } from '../../services/apiService';
import axios, { AxiosError } from 'axios';

// Ensure this path is correct for your shared types
import { 
  ParsedResumeData, 
  SkillObject, 
  WorkExperienceItem, 
  OrganizationExperienceSummary,
  EducationItem, 
  CertificationItem, 
  TimeSpentInOrgItem,
  KeywordMatchDetail, 
  MissingDetail,
  WorkExperiencesContainer, // <<<<< Ensure this is imported for type narrowing
  ProjectExperienceMetadata // <<<<< Ensure this is imported
} from '../../types/analyseResumeTypes'; // <<<<< VERIFY THIS PATH

// SectionTitle Helper Component (same as before)
const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Typography variant="h6" component="h3" gutterBottom sx={{ mt: 2, mb: 1, fontWeight: 'bold', color: 'primary.main' }}>
    {children}
  </Typography>
);

interface AnalyseResumeFormProps {
  uploadEndpoint: string;
  cardTitle?: string;
}

const AnalyseResumeForm: React.FC<AnalyseResumeFormProps> = ({ uploadEndpoint, cardTitle = "Analyse Resume" }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);
  const [parsedData, setParsedData] = useState<ParsedResumeData | null>(null);
  const theme = useTheme();

  const allowedFileTypes = ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
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

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage({ type: 'info', text: 'Please select a file to upload first.' });
      return;
    }

    setUploading(true);
    setMessage(null);
    setParsedData(null);

    const formData = new FormData();
    formData.append('resume', selectedFile);

    try {
      // const response = await uploadResumeV2Api(formData); 
      const response = await uploadResumeApiv3(formData); 
      
      const result: ParsedResumeData = response.data;
      const successMessage = result.db_id ? `Resume for ${result.name || 'candidate'} (ID: ${result.db_id || 'N/A'}) parsed and analysed!` : 'Resume uploaded and parsed!';
      
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

  const renderSkillChips = (skillsArray?: string[]) => {
    if (!skillsArray || skillsArray.length === 0) {
      return <Typography variant="body2" color="text.secondary">N/A</Typography>;
    }
    return skillsArray.map((skill: string, index: number) => {
      return (
        <Chip 
          key={`${skill}-${index}`} 
          label={skill} 
          sx={{ mr: 0.5, mb: 0.5 }} 
          variant="outlined" 
          size="small" 
        />
      );
    }).filter(Boolean);
  };

  const renderKeywordDetails = (details?: Record<string, KeywordMatchDetail[] | MissingDetail[]>) => {
    if (!details || Object.keys(details).length === 0) return <Typography variant="body2" color="text.secondary">N/A</Typography>;
    
    return Object.entries(details).map(([category, items]) => (
      items && items.length > 0 && (
        <Box key={category} sx={{ mb: 1 }}>
          <Typography variant="subtitle2" sx={{ textTransform: 'capitalize', fontWeight: 'medium' }}>
            {category.replace(/_/g, ' ')}:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
            {items.map((item: KeywordMatchDetail | MissingDetail, idx: number) => (
              <Chip key={`${category}-${idx}`} label={item.keyword || 'N/A'} size="small" variant="filled" color="primary" sx={{opacity:0.8}} />
            ))}
          </Box>
        </Box>
      )
    )).filter(Boolean);
  };

  const workExperiences = parsedData?.plugin_data?.project_experience && 
                          parsedData.plugin_data.project_experience.length > 0 &&
                          (parsedData.plugin_data.project_experience[0] as WorkExperiencesContainer)?.work_experiences;

  return (
    <>
      <Card
        sx={{
          width: '100%',
          margin: 'auto',
          mb: 1,
          borderRadius: 0,
          boxShadow: 2,
          p: 1,
        }}
      >
        <CardContent sx={{ p: { xs: 1, sm: 1.5 }, '&:last-child': { pb: { xs: 1, sm: 1.5 } } }}>
          <Typography
            variant="h6"
            component="h2"
            sx={{ textAlign: 'center', mb: 2 }}
          >
            {cardTitle}
          </Typography>

          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              alignItems: 'center',
              justifyContent: 'center',
              gap: { xs: 1, sm: 1.5 },
              mb: 1.5
            }}
          >
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <input
                accept=".docx"
                style={{ display: 'none' }}
                id="resume-upload-button"
                type="file"
                onChange={handleFileChange}
                disabled={uploading}
              />
              <label htmlFor="resume-upload-button">
                <Button
                  variant="outlined"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  disabled={uploading}
                  size="small"
                  sx={{ py: 0.5, px: 1.5 }}
                >
                  {selectedFile ? 'Change .docx File' : 'Choose .docx File'}
                </Button>
              </label>
            </Box>

            <Button
              variant="contained"
              color="primary"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              startIcon={uploading ? null : <CloudUploadIcon />}
              size="small"
              sx={{ py: 0.5, px: 1.5, width: { xs: 'auto', sm: 'auto'} }}
            >
              {uploading ? 'Uploading...' : 'Upload & Analyse'}
            </Button>
          </Box>

          {selectedFile && (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, my: 1, width: '100%' }}>
              <InsertDriveFileIcon color="action" sx={{fontSize: '1rem', flexShrink: 0}} />
              <Typography
                variant="caption"
                color="text.primary"
                noWrap
                title={selectedFile.name}
                sx={{
                  maxWidth: 'calc(100% - 40px)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {selectedFile.name} ({Math.round(selectedFile.size / 1024)} KB)
              </Typography>
            </Box>
          )}

          {uploading && (
            <LinearProgress variant="indeterminate" sx={{ width: '100%', my: 1.5 }} />
          )}

          {message && (
            <Alert
              severity={message.type}
              sx={{
                width: '100%',
                my: 1.5,
                py: 0.25,
                fontSize: '0.75rem',
                '& .MuiAlert-icon': { fontSize: '1.1rem', mr: 0.5, alignItems: 'center' },
                '& .MuiAlertTitle-root': { fontSize: '0.85rem', mb: 0.1, fontWeight: 'medium' }
              }}
            >
              <AlertTitle>{message.type === 'success' ? 'Success' : message.type === 'error' ? 'Error' : 'Info'}</AlertTitle>
              {message.text}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Parsed Data Display Section */}
      {parsedData && (
        <Paper
          elevation={2}
          sx={{
            p: {xs: 2, sm: 3},
            mt: 3,
            borderRadius: 0,
            border: (th: Theme) => `1px solid ${th.palette.divider}`
          }}
        >
          <Typography variant="h5" component="h2" gutterBottom sx={{ textAlign: 'center', mb: 2, color: 'primary.dark' }}>
            Analysed Resume Details
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={3}>
            {/* Basic Information & Overview */}
            <Grid item xs={12} md={6}>
              <SectionTitle>👤 Basic Information</SectionTitle>
              <Typography variant="subtitle1" gutterBottom><strong>Name:</strong> {parsedData.name || 'N/A'}</Typography>
              {parsedData.email && <Typography variant="body2" sx={{mb:0.5}}><strong>Email:</strong> {parsedData.email}</Typography>}
              {parsedData.contact_number && <Typography variant="body2" sx={{mb:0.5}}><strong>Phone:</strong> {parsedData.contact_number}</Typography>}
              {parsedData.contact?.linkedin && <Typography variant="body2" sx={{mb:0.5}}><strong>LinkedIn:</strong> <a href={parsedData.contact.linkedin} target="_blank" rel="noopener noreferrer">{parsedData.contact.linkedin}</a></Typography>}
              {parsedData.contact?.github && <Typography variant="body2" sx={{mb:0.5}}><strong>GitHub:</strong> <a href={parsedData.contact.github} target="_blank" rel="noopener noreferrer">{parsedData.contact.github}</a></Typography>}
            </Grid>
            <Grid item xs={12} md={6}>
              <SectionTitle>📈 Experience Overview</SectionTitle>
              <Typography variant="body2" gutterBottom><strong>Total Experience:</strong> {parsedData.YoE || 'N/A'}</Typography>
              <Typography variant="body2" gutterBottom><strong>Organization Switches:</strong> {parsedData.organization_switches !== undefined ? parsedData.organization_switches : 'N/A'}</Typography>
            </Grid>
            <Grid item xs={12}><SectionTitle>📝 Summary</SectionTitle><Typography variant="body2" sx={{ whiteSpace: 'pre-line', textAlign: 'justify', lineHeight: 1.6 }}>{parsedData.summary || 'N/A'}</Typography></Grid>

          {/* Detailed Work History - From root-level work_experiences */}
            {parsedData.work_experiences && parsedData.work_experiences.length > 0 && ( 
              <Grid item xs={12}>
                <SectionTitle>💼 Detailed Work History</SectionTitle>
                {parsedData.work_experiences.map((exp: OrganizationExperienceSummary, index: number) => ( // <<<<< USE OrganizationExperienceSummary
                  <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">{exp.role || 'Role N/A'} at {exp.company || 'Company N/A'}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{mb:1}}>{exp.start_date || 'Date N/A'} - {exp.end_date || 'Date N/A'} {exp.location && `| ${exp.location}`}</Typography>
                    {/* Check if 'information' or 'description' exist in OrganizationExperienceSummary */}
                    {(exp as WorkExperienceItem).information && <Typography variant="body2" color="text.secondary" sx={{whiteSpace: 'pre-line', lineHeight: 1.6}}>{(exp as WorkExperienceItem).information}</Typography>}
                    {(exp as WorkExperienceItem).description && <Typography variant="body2" color="text.secondary" sx={{whiteSpace: 'pre-line', lineHeight: 1.6}}>{(exp as WorkExperienceItem).description}</Typography>}
                    {/* Check for technologies if they might exist in OrganizationExperienceSummary */}
                    {(exp as WorkExperienceItem).technologies && (exp as WorkExperienceItem).technologies!.length > 0 && (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt:1.5 }}>
                            {(exp as WorkExperienceItem).technologies!.map((tech: string, techIndex: number) => (
                                <Chip key={techIndex} label={tech} size="small" variant="filled" sx={{bgcolor: 'grey.200', fontWeight:'medium', mr:0.5, mb:0.5}} />
                            ))}
                        </Box>
                    )}
                  </Paper>
                ))}
              </Grid>
            )}

            {/* Work Experience - Now correctly typed and accessed */}
            {workExperiences && workExperiences.length > 0 && ( // Use the extracted and narrowed 'workExperiences' variable
              <Grid item xs={12}>
                <SectionTitle>💼 Work Experience</SectionTitle>
                {workExperiences.map((exp: WorkExperienceItem, index: number) => ( // Now 'exp' is correctly WorkExperienceItem
                  <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">{exp.role || 'Role N/A'}</Typography>
                    <Typography variant="body1" color="text.primary" gutterBottom>{exp.company || 'Company N/A'}</Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{mb:1}}>{exp.start_date || 'Date N/A'} - {exp.end_date || 'Date N/A'} {exp.location && `| ${exp.location}`}</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{whiteSpace: 'pre-line', lineHeight: 1.6}}>{exp.information || 'N/A'}</Typography>
                    {exp.technologies && exp.technologies.map((tech: string, techIndex: number) => (
                        <Chip key={techIndex} label={tech} size="small" variant="filled" sx={{bgcolor: 'grey.200', fontWeight:'medium', mr:0.5, mb:0.5}} />
                    ))}
                  </Paper>
                ))}
              </Grid>
            )}

            {/* Skills Section */}
            {parsedData.skills && parsedData.skills.length > 0 && ( 
              <Grid item xs={12}>
                <SectionTitle>🛠️ Skills</SectionTitle>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {parsedData.skills.map((skill: string, index: number) => (
                    <Chip key={index} label={skill} sx={{ mr: 0.5, mb: 0.5 }} variant="outlined" size="small" />
                  ))}
                </Box>
              </Grid>
            )}

            {/* Education */}
            {parsedData.educations && parsedData.educations.length > 0 && ( 
              <Grid item xs={12} md={6}>
                <SectionTitle>🎓 Education</SectionTitle>
                <List dense disablePadding>
                  {parsedData.educations.map((edu: EducationItem, index: number) => (
                    <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                      <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={edu.degree || 'Degree N/A'} secondary={`${edu.institution || 'Institution N/A'} ${edu.start_date ? `(${edu.start_date} - ${edu.end_date || 'Present'})` : ''}`} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}

            {/* Certifications */}
            {parsedData.certifications && parsedData.certifications.length > 0 && (
              <Grid item xs={12} md={6}>
                <SectionTitle>📜 Certifications</SectionTitle>
                <List dense disablePadding>
                  {parsedData.certifications.map((cert: CertificationItem, index: number) => (
                    <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                      <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={cert.name || 'Unnamed Certification'} secondary={`${cert.issuing_organization || 'N/A'} ${cert.date ? `(${cert.date})` : ''}`} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            )}

            {/* Plugin Data - Keyword Matcher */}
            {parsedData.plugin_data?.keyword_matcher && (
              <Grid item xs={12}>
                <SectionTitle>🔍 Keyword Matcher</SectionTitle>
                <Box sx={{ mb: 1.5 }}>
                  <Typography variant="body2" gutterBottom><strong>Overall Match Score:</strong> {parsedData.plugin_data.keyword_matcher.overall_match_score !== undefined ? `${parsedData.plugin_data.keyword_matcher.overall_match_score.toFixed(2)}%` : 'N/A'}</Typography>
                  <Typography variant="body2" gutterBottom><strong>Total Achieved Score:</strong> {parsedData.plugin_data.keyword_matcher.total_achieved_score !== undefined ? parsedData.plugin_data.keyword_matcher.total_achieved_score : 'N/A'}</Typography>
                  <Typography variant="body2" gutterBottom><strong>Total Possible Score:</strong> {parsedData.plugin_data.keyword_matcher.total_possible_score !== undefined ? parsedData.plugin_data.keyword_matcher.total_possible_score : 'N/A'}</Typography>
                </Box>
                {renderKeywordDetails(parsedData.plugin_data.keyword_matcher.matched_details)}
                <Box mt={2}> {/* Add some spacing between matched and missing */}
                  {renderKeywordDetails(parsedData.plugin_data.keyword_matcher.missing_details)}
                </Box>
              </Grid>
            )}

            {/* Technology Experience Years */}
            {parsedData.technology_experience_years && Object.keys(parsedData.technology_experience_years).length > 0 && (
                <Grid item xs={12}> <SectionTitle>💡 Technology Experience (Years)</SectionTitle>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {Object.entries(parsedData.technology_experience_years).map(([tech, years]: [string, number], index: number) => (
                            <Chip key={index} label={`${tech}: ${years} yrs`} variant="filled" sx={{bgcolor: 'grey.300', fontWeight:'medium'}} />
                        ))}
                    </Box>
                </Grid>
            )}

            {/* Time Spent In Organizations */}
            {parsedData.time_spent_in_org && parsedData.time_spent_in_org.length > 0 && (
                <Grid item xs={12}> <SectionTitle>🏢 Time Spent In Organizations</SectionTitle>
                    <List dense disablePadding>
                        {parsedData.time_spent_in_org.map((org_time: TimeSpentInOrgItem, index: number) => (
                            <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5}}>
                                <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={org_time.company_name || "N/A"} secondary={`Years: ${org_time.total_duration_years?.toFixed(1) || 'N/A'}, Months: ${org_time.total_duration_months?.toFixed(1) || 'N/A'}`} />
                            </ListItem>
                        ))}
                    </List>
                </Grid>
            )}
          </Grid>
        </Paper>
      )}
    </>
  );
};

export default AnalyseResumeForm;