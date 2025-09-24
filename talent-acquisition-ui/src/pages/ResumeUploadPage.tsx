// src/pages/ResumeUploadPage.tsx
import React from 'react';
import ResumeUploadForm from '../components/resume_upload/ResumeUploadForm';
import PageContainer from '../components/common/PageContainer';

const ResumeUploadPage: React.FC = () => {
  return (
    <PageContainer>
      <ResumeUploadForm />
    </PageContainer>
  );
};

export default ResumeUploadPage;