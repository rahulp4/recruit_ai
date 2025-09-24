// src/components/resume_upload/ParsedResumeDisplay.tsx
import React from 'react';
import { Box, Typography, Chip, Paper, Grid, Divider, List, ListItem, ListItemText } from '@mui/material';
import { Theme } from '@mui/material/styles';

// PASTE THE IDENTICAL SkillObject and ParsedResumeData interfaces from above here
interface SkillObject {
  name: string;
  experience_years?: number | null;
}

interface ParsedResumeData {
  name?: string;
  summary?: string;
  total_experience_years?: number;
  contact?: { /* ... */ email?: string; phone?: string; linkedin?: string | null; github?: string | null; website?: string | null; location?: string; };
  experience?: Array<{ /* ... */ title?: string | null; company?: string; location?: string | null; from?: string; to?: string; description?: string; technologies?: string[]; }>;
  skills?: {
    languages?: Array<SkillObject>;
    frameworks?: Array<SkillObject>;
    databases?: Array<SkillObject>;
    tools?: Array<SkillObject>;
    platforms?: Array<SkillObject>;
    methodologies?: Array<SkillObject>;
    other?: Array<SkillObject>;
  };
  projects?: Array<{ /* ... */ name?: string; description?: string; technologies?: string[]; }>;
  education?: Array<{ /* ... */ degree?: string; field_of_study?: string | null; institution?: string | null; location?: string | null; dates?: string; }>;
  certifications?: Array<{ /* ... */ name?: string; issuing_organization?: string | null; date?: string; }>;
  organization_switches?: number;
  technology_experience_years?: Record<string, number>;
  time_spent_in_org?: Array<{ /* ... */ company_name?: string; total_duration_years?: number; total_duration_months?: number; }>;
  db_id?: number;
}


interface ParsedResumeDisplayProps {
  data: ParsedResumeData | null;
}

const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Typography variant="h6" component="h3" gutterBottom sx={{ mt: 2, mb: 1, fontWeight: 'bold', color: 'primary.main' }}>
    {children}
  </Typography>
);

const ParsedResumeDisplay: React.FC<ParsedResumeDisplayProps> = ({ data }) => {
  if (!data) {
    return null;
  }

  const renderSkillChips = (skillsArray?: Array<SkillObject>) => {
    if (!skillsArray || skillsArray.length === 0) {
      return <Typography variant="body2" color="text.secondary">N/A</Typography>;
    }
    
    return skillsArray.map((skillItem, index) => {
      if (skillItem && typeof skillItem.name === 'string') {
        let chipLabel = skillItem.name;
        if (skillItem.experience_years !== undefined && skillItem.experience_years !== null) {
          chipLabel += ` (${skillItem.experience_years} yr${skillItem.experience_years === 1 ? '' : 's'})`;
        }

        // ----- START DEBUG LOG -----
        console.log(`Rendering Chip for skill:`, 
                    `Item Original: ${JSON.stringify(skillItem)}`,
                    `Derived Label: "${chipLabel}"`, 
                    `Type of Label: ${typeof chipLabel}`);
        // ----- END DEBUG LOG -----

        if (typeof chipLabel !== 'string') {
            // This case should ideally not be hit if the above logic is correct
            // and skillItem.name is always a string for these objects.
            console.error("Chip label is not a string!", chipLabel, "Original item:", skillItem);
            return null; // Prevent rendering with a non-string label
        }

        return (
          <Chip 
            key={`${chipLabel}-${index}`} // Make sure key is unique
            label={chipLabel} 
            sx={{ mr: 0.5, mb: 0.5 }} 
            variant="outlined" 
            size="small" 
          />
        );
      }
      console.warn("Skipping skill item due to unexpected format or missing/invalid name property:", skillItem);
      return null; 
    }).filter(Boolean); 
  };

  // ... rest of the ParsedResumeDisplay component (Grid, Sections, etc.)
  // Ensure it's exactly as the last correct version you had that displayed other fields.
  // For brevity, I'm not re-pasting the entire return statement if only renderSkillChips and interfaces changed.
  // The return (...) part from the previous correct response should be used here.
  // Make sure the call to renderSkillChips uses the correct cast:
  // {renderSkillChips(skillsList as Array<SkillObject>)}

  return (
    <Paper 
      elevation={2} 
      sx={{ 
        p: {xs: 2, sm: 3}, 
        mt: 3, 
        borderRadius: 0,
        border: (theme: Theme) => `1px solid ${theme.palette.divider}`
      }}
    >
      <Typography variant="h5" component="h2" gutterBottom sx={{ textAlign: 'center', mb: 2, color: 'primary.dark' }}>
        Parsed Resume Details (ID: {data.db_id || 'N/A'})
      </Typography>
      <Divider sx={{ mb: 2 }} />
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <SectionTitle>👤 Basic Information</SectionTitle>
          <Typography variant="subtitle1" gutterBottom><strong>Name:</strong> {data.name || 'N/A'}</Typography>
          {data.contact?.email && <Typography variant="body2" sx={{mb:0.5}}><strong>Email:</strong> {data.contact.email}</Typography>}
          {data.contact?.phone && <Typography variant="body2" sx={{mb:0.5}}><strong>Phone:</strong> {data.contact.phone}</Typography>}
          {data.contact?.location && <Typography variant="body2" sx={{mb:0.5}}><strong>Location:</strong> {data.contact.location}</Typography>}
          {data.contact?.linkedin && <Typography variant="body2" sx={{mb:0.5}}><strong>LinkedIn:</strong> <a href={data.contact.linkedin} target="_blank" rel="noopener noreferrer">{data.contact.linkedin}</a></Typography>}
          {data.contact?.github && <Typography variant="body2" sx={{mb:0.5}}><strong>GitHub:</strong> <a href={data.contact.github} target="_blank" rel="noopener noreferrer">{data.contact.github}</a></Typography>}
        </Grid>
        <Grid item xs={12} md={6}>
           <SectionTitle>📈 Experience Overview</SectionTitle>
           <Typography variant="body2" gutterBottom>
            <strong>Total Experience:</strong> {data.total_experience_years !== undefined ? `${data.total_experience_years} years` : 'N/A'}
          </Typography>
          <Typography variant="body2" gutterBottom>
            <strong>Organization Switches:</strong> {data.organization_switches !== undefined ? data.organization_switches : 'N/A'}
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <SectionTitle>📝 Summary</SectionTitle>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-line', textAlign: 'justify', lineHeight: 1.6 }}>{data.summary || 'N/A'}</Typography>
        </Grid>
        {data.experience && data.experience.length > 0 && (
          <Grid item xs={12}>
            <SectionTitle>💼 Work Experience</SectionTitle>
            {data.experience.map((exp, index) => (
              <Paper key={index} variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 1 }}>
                <Typography variant="subtitle1" fontWeight="bold">{exp.title || 'Role N/A'}</Typography>
                <Typography variant="body1" color="text.primary" gutterBottom>{exp.company || 'Company N/A'}</Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{mb:1}}>{exp.from || 'Date N/A'} - {exp.to || 'Date N/A'} {exp.location && `| ${exp.location}`}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{whiteSpace: 'pre-line', lineHeight: 1.6}}>{exp.description || 'N/A'}</Typography>
                {exp.technologies && exp.technologies.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt:1.5 }}>
                    {exp.technologies.map(tech => <Chip key={tech} label={tech} size="small" variant="filled" sx={{bgcolor: 'grey.200', fontWeight:'medium'}} />)}
                  </Box>
                )}
              </Paper>
            ))}
          </Grid>
        )}
        {data.skills && (
          <Grid item xs={12}>
            <SectionTitle>🛠️ Skills</SectionTitle>
            {Object.entries(data.skills).map(([category, skillsList]) => (
              Array.isArray(skillsList) && skillsList.length > 0 && (
                <Box key={category} sx={{ mb: 1.5 }}>
                  <Typography variant="subtitle2" sx={{ textTransform: 'capitalize', fontWeight: 500, mb: 0.5 }}>{category.replace(/_/g, ' ')}:</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {renderSkillChips(skillsList as Array<SkillObject>)}
                  </Box>
                </Box>
              )
            ))}
          </Grid>
        )}
        {data.education && data.education.length > 0 && (
           <Grid item xs={12} md={6}>
            <SectionTitle>🎓 Education</SectionTitle>
            <List dense disablePadding>
              {data.education.map((edu, index) => (
                <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                  <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={`${edu.degree || 'Degree N/A'}${edu.field_of_study ? ` in ${edu.field_of_study}` : ''}`} secondary={`${edu.institution || 'Institution N/A'} ${edu.dates ? `(${edu.dates})` : ''}`} />
                </ListItem>
              ))}
            </List>
          </Grid>
        )}
        {data.certifications && data.certifications.length > 0 && (
          <Grid item xs={12} md={6}>
            <SectionTitle>📜 Certifications</SectionTitle>
            <List dense disablePadding>
              {data.certifications.map((cert, index) => (
                <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5, alignItems: 'flex-start'}}>
                  <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={cert.name || 'Unnamed Certification'} secondary={`${cert.issuing_organization || 'N/A'} ${cert.date ? `(${cert.date})` : ''}`} />
                </ListItem>
              ))}
            </List>
          </Grid>
        )}
        {data.technology_experience_years && Object.keys(data.technology_experience_years).length > 0 && (
            <Grid item xs={12}>
                <SectionTitle>💡 Technology Experience (Years)</SectionTitle>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {Object.entries(data.technology_experience_years).map(([tech, years]) => (
                        <Chip key={tech} label={`${tech}: ${years} yrs`} variant="filled" sx={{bgcolor: 'grey.300', fontWeight:'medium'}} />
                    ))}
                </Box>
            </Grid>
        )}
         {data.time_spent_in_org && data.time_spent_in_org.length > 0 && (
            <Grid item xs={12}>
                <SectionTitle>🏢 Time Spent In Organizations</SectionTitle>
                 <List dense disablePadding>
                    {data.time_spent_in_org.map((org_time, index) => (
                        <ListItem key={index} disableGutters sx={{display: 'block', mb: 0.5}}>
                             <ListItemText primaryTypographyProps={{fontWeight: 'medium'}} primary={org_time.company_name || "N/A"} secondary={`Years: ${org_time.total_duration_years?.toFixed(1) || 'N/A'}, Months: ${org_time.total_duration_months?.toFixed(1) || 'N/A'}`} />
                        </ListItem>
                    ))}
                </List>
            </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default ParsedResumeDisplay;