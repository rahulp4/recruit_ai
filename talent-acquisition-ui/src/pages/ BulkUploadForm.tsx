import React from 'react';
import BulkUploadForm from '../components/bulk_upload/ BulkUploadForm';
import PageContainer from '../components/common/PageContainer';

const BulkUploadPage: React.FC = () => {
  return (
    <PageContainer>
      <BulkUploadForm />
    </PageContainer>
  );
};

export default BulkUploadPage;