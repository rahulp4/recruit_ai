// src/pages/CreateUserPage.tsx
import React, { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import CreateUserForm from '../components/user_management/CreateUserForm';
import PageContainer from '../components/common/PageContainer';
import StatusAlert from '../components/common/StatusAlert';
import { getOrganizationsApi } from '../services/apiService';
import { Organization } from '../types/jobDescriptionTypes';
import { useAuth } from '../hooks/useAuth';

const CreateUserPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrgs = async () => {
      if (!isAuthenticated) {
        setError('You must be logged in to create users.');
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        const response = await getOrganizationsApi();
        setOrganizations(response.data.organizations || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch organizations:', err);
        setError('Failed to load organizations. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrgs();
  }, [isAuthenticated]);

  const userRoles = ['admin', 'hr_manager', 'recruiter']; // This could come from a config or API in the future

  return (
    <PageContainer title="User Management - Create User">
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <StatusAlert message={{ type: 'error', text: error }} />
      ) : (
        <CreateUserForm organizations={organizations} roles={userRoles} />
      )}
    </PageContainer>
  );
};

export default CreateUserPage;
