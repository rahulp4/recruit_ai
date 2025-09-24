// src/pages/AnalyseResumePage.tsx
import React from 'react';
import { Box } from '@mui/material';
import AnalyseResumeForm from '../components/analyse_resume/AnalyseResumeForm'; // <<<<< IMPORT NEW FORM

const AnalyseResumePage: React.FC = () => {
  return (
    <Box sx={{ width: '100%', py: 2 }}>
      {/* Render the new form component with its specific endpoint */}
      <AnalyseResumeForm uploadEndpoint="/v2/upload_resume" cardTitle="Analyse & Process Resume" />
    </Box>
  );
};

export default AnalyseResumePage;