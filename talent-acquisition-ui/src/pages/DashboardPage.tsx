// src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography, Box, Avatar } from '@mui/material';
import { Theme, useTheme } from '@mui/material/styles'; // Import Theme and useTheme

import ShowChartIcon from '@mui/icons-material/ShowChart';
import GroupIcon from '@mui/icons-material/Group';
import WorkHistoryIcon from '@mui/icons-material/WorkHistory';

import { getActiveJobDescriptionCountApi, getActiveProfileCountApi } from '../services/apiService';
import PageContainer from '../components/common/PageContainer';
import TitledCard from '../components/common/TitledCard';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactElement; // Icon is a ReactElement, expected to be pre-styled if needed
  color?: string; // e.g., "primary.main", "secondary.main", "success.main" for Avatar background
}

// StatCard will now simply render the icon it receives.
// The responsibility of styling the icon (e.g., its color) is moved to where StatCard is used.
const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color = "primary.main" }) => {
  // No need for useTheme() here if icon styling is handled outside
  return (
    <Card sx={{ display: 'flex', alignItems: 'center', p: 2.5, height: '100%' }}>
      <Avatar sx={{ bgcolor: color, width: 52, height: 52, mr: 2 }}>
        {icon} {/* Render the icon directly as passed */}
      </Avatar>
      <Box>
        <Typography variant="body1" color="text.secondary" gutterBottom>{title}</Typography>
        <Typography variant="h5" component="div" fontWeight="bold">{value}</Typography>
      </Box>
    </Card>
  );
};

const DashboardPage: React.FC = () => {
  const theme = useTheme(); // useTheme hook for access to theme, e.g., for theme.palette.common.white
  const [activeJobCount, setActiveJobCount] = useState<number | null>(null);
  const [isJobsLoading, setIsJobsLoading] = useState<boolean>(true);
  const [jobsError, setJobsError] = useState<string | null>(null);

  const [activeProfileCount, setActiveProfileCount] = useState<number | null>(null);
  const [isProfilesLoading, setIsProfilesLoading] = useState<boolean>(true);
  const [profilesError, setProfilesError] = useState<string | null>(null);

  useEffect(() => {
    const fetchActiveJobCount = async () => {
      try {
        setIsJobsLoading(true);
        const response = await getActiveJobDescriptionCountApi();
        setActiveJobCount(response.data.activeJobDescriptionCount);
        setJobsError(null); // Clear any previous errors
      } catch (err: any) {
        setJobsError(err.response?.data?.error || 'Failed to fetch active job count.');
        setActiveJobCount(null); // Clear data on error
      } finally {
        setIsJobsLoading(false);
      }
    };

    const fetchActiveProfileCount = async () => {
      try {
        setIsProfilesLoading(true);
        const response = await getActiveProfileCountApi();
        setActiveProfileCount(response.data.profileCount);
        setProfilesError(null);
      } catch (err: any) {
        setProfilesError(err.response?.data?.error || 'Failed to fetch profile count.');
        setActiveProfileCount(null);
      } finally {
        setIsProfilesLoading(false);
      }
    };

    fetchActiveJobCount();
    fetchActiveProfileCount();
  }, []); // Empty dependency array means this runs once on mount

  return (
    <PageContainer>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Active Candidates"
            value={isProfilesLoading ? '...' : (profilesError || activeProfileCount?.toLocaleString()) ?? 'N/A'}
            // Style the icon here when passing it as a prop
            icon={<GroupIcon sx={{ color: theme.palette.common.white }} />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Open Positions"
            value={isJobsLoading ? '...' : (jobsError || activeJobCount?.toString()) ?? 'N/A'}
            icon={<WorkHistoryIcon sx={{ color: theme.palette.common.white }} />}
            color="secondary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Interviews Today"
            value="12"
            icon={<ShowChartIcon sx={{ color: theme.palette.common.white }} />}
            color="success.main" // Ensure your theme has palette.success.main defined
          />
        </Grid>

        <Grid item xs={12} lg={8}>
          <TitledCard title="Monthly Application Trends">
            <Box sx={{ height: 280, bgcolor: 'action.hover', borderRadius: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Typography variant="caption" color="text.secondary">Chart Placeholder</Typography>
            </Box>
          </TitledCard>
        </Grid>

        <Grid item xs={12} lg={4}>
          <TitledCard title="Recent Activity">
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" paragraph>• New candidate 'John Doe' added.</Typography>
              <Typography variant="body2" paragraph>• Job 'Senior Developer' status changed.</Typography>
              <Typography variant="body2" paragraph>• Interview scheduled for 'Jane Smith'.</Typography>
              <Typography variant="body2" paragraph>• Offer extended to 'Alice Brown'.</Typography>
            </Box>
          </TitledCard>
        </Grid>
      </Grid>
    </PageContainer>
  );
};

export default DashboardPage;