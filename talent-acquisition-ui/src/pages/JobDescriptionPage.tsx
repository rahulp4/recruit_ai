// src/pages/JobDescriptionPage.tsx
import React, { useState, useEffect } from 'react';
import {
  Select, MenuItem, FormControl, InputLabel, Button,
  TableContainer, Table, TableHead, TableRow, TableBody,
  TextField, Grid, Skeleton, LinearProgress, CircularProgress
} from '@mui/material'; 
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SearchIcon from '@mui/icons-material/Search';

import { getOrganizationsApi, uploadJobDescriptionApi, getJobDescriptionsApi ,semanticSearchJobDescriptionsApi} from '../services/apiService';
import { styled } from '@mui/material/styles';
import TableCell, { tableCellClasses } from '@mui/material/TableCell';
import { Organization, JobDescription } from '../types/jobDescriptionTypes';
import { useAuth } from '../hooks/useAuth';

import DocxUploadModal from '../components/common/DocxUploadModal';
import RuleOverlayDialog from '../components/common/RuleOverlayDialog'; // Adjust path if needed
import TitledCard from '../components/common/TitledCard';
import StatusAlert, { StatusMessage } from '../components/common/StatusAlert';
import PageContainer from '../components/common/PageContainer';

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  [`&.${tableCellClasses.head}`]: {
    backgroundColor: '#EBF3FE',
    color: theme.palette.text.primary,
    fontWeight: 'bold',
  },
  [`&.${tableCellClasses.body}`]: {
    fontSize: 14,
  },
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  // hide last border
  '&:last-child td, &:last-child th': {
    border: 0,
  },
}));

const JobDescriptionPage: React.FC = () => {
  const { appUser, isAuthenticated } = useAuth();

  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [jobDescriptionText, setJobDescriptionText] = useState('');
  const [jobDescriptions, setJobDescriptions] = useState<JobDescription[]>([]);
  const [uploading, setUploading] = useState(false);
  const [loadingJds, setLoadingJds] = useState(false);
  const [message, setMessage] = useState<StatusMessage | null>(null);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [ruleDialogOpen, setRuleDialogOpen] = useState(false);
  const [selectedRuleJobId, setSelectedRuleJobId] = useState<string | null>(null);

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await getOrganizationsApi();

        if (response.status >= 200 && response.status < 300) {
          const fetchedOrgs: Organization[] = response.data.organizations;
          setOrganizations(fetchedOrgs);

          let selectedId = '';
          if (appUser!.organizationId && fetchedOrgs.some(org => org.id === appUser!.organizationId)) {
            selectedId = appUser!.organizationId;
          } else if (fetchedOrgs.length === 1) {
            selectedId = fetchedOrgs[0].id;
          }

          setSelectedOrgId(selectedId);

          if (selectedId) {
            setLoadingJds(true);
            try {
              const jdResponse = await getJobDescriptionsApi(selectedId);
              setJobDescriptions(jdResponse.data);
            } catch {
              setMessage({ type: 'error', text: 'Failed to load job descriptions.' });
            } finally {
              setLoadingJds(false);
            }
          }
        }
      } catch {
        setMessage({ type: 'error', text: 'Failed to load organizations.' });
      }
    };
    fetchOrganizations();
  }, [appUser]);

  const handleTextareaUpload = async () => {
    setUploading(true);
    const blob = new Blob([jobDescriptionText], { type: 'text/plain' });
    const formData = new FormData();
    formData.append('jd_file', blob, 'job_description.txt');
    try {
      const response = await uploadJobDescriptionApi(selectedOrgId, formData);
      if (response.status >= 200 && response.status < 300) {
        setMessage({ type: 'success', text: 'Text-based JD uploaded successfully!' });
        setJobDescriptionText('');
        const refresh = await getJobDescriptionsApi(selectedOrgId);
        setJobDescriptions(refresh.data);
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to upload JD.' });
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!selectedOrgId) {
      setMessage({ type: 'error', text: 'Please select an organization before uploading.' });
      return;
    }
    setUploading(true);
    setUploadModalOpen(false); // Close modal once upload starts
    setMessage({ type: 'info', text: `Uploading and analyzing ${file.name}...` });

    const formData = new FormData();
    formData.append('jd_file', file, file.name);
    try {
      const response = await uploadJobDescriptionApi(selectedOrgId, formData);
      if (response.status >= 200 && response.status < 300) {
        setMessage({ type: 'success', text: 'File processed successfully! Refreshing list...' });
        const refresh = await getJobDescriptionsApi(selectedOrgId);
        setJobDescriptions(refresh.data);
      } else {
        setMessage({ type: 'error', text: `Upload failed with status: ${response.status}` });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Upload failed. Please try again.' });
      console.error('File upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const isSearchEnabled = organizations.length >= 1;
  const isUploadEnabled = !!selectedOrgId && !uploading;

  return (
    <PageContainer>
      {uploading && <LinearProgress sx={{ position: 'absolute', top: 0, left: 0, right: 0 }} />}
      <StatusAlert
        message={message}
        onClose={() => setMessage(null)}
      />
      <TitledCard title="Job Description Management">
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel id="org-label">Org Name</InputLabel>
              <Select
                labelId="org-label"
                value={selectedOrgId}
                onChange={async (e) => {
                  const newOrgId = e.target.value;
                  setSelectedOrgId(newOrgId);
                  setJobDescriptions([]);
                  setLoadingJds(true);
                  try {
                    const jdResponse = await getJobDescriptionsApi(newOrgId);
                    setJobDescriptions(jdResponse.data);
                  } catch {
                    setMessage({ type: 'error', text: 'Failed to load job descriptions.' });
                  } finally {
                    setLoadingJds(false);
                  }
                }}
                label="Org Name"
              >
                {organizations.map((org) => (
                  <MenuItem key={org.id} value={org.id}>
                    {org.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={8}>
            <TextField
              fullWidth
              multiline
              minRows={2}
              maxRows={2}
              label="Enter query for semantic search"
              variant="outlined"
              value={jobDescriptionText}
              onChange={(e) => setJobDescriptionText(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={async () => {
                if (!jobDescriptionText.trim()) {
                  setMessage({ type: 'error', text: 'Please enter a query for semantic search.' });
                  return;
                }
                setJobDescriptions([]);
                setLoadingJds(true);
                try {
                const response = await semanticSearchJobDescriptionsApi(jobDescriptionText);
                  if (response.status === 200) {
                    setJobDescriptions(response.data); // ✅ response.data is already JobDescription[]
                    setMessage({ type: 'success', text: `Found ${response.data.length} matches.` });
                  } else {
                    setJobDescriptions([]);
                    setMessage({ type: 'error', text: 'Search failed. Try again.' });
                  }
                } catch (err) {
                  setJobDescriptions([]);
                  setMessage({ type: 'error', text: 'An error occurred during search.' });
                } finally {
                  setLoadingJds(false);
                }
              }}
              disabled={!isSearchEnabled}
            >
              Search
            </Button>
              <Button
                variant="contained"
                endIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
                onClick={() => setUploadModalOpen(true)}
                disabled={!isUploadEnabled}
              >
                {uploading ? 'Processing...' : 'Upload and Analyse'}
              </Button>
          </Grid>
        </Grid>
      </TitledCard>

      {loadingJds && (
        <TitledCard title="Loading Job Descriptions..." disableContentPadding>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <StyledTableCell>ID</StyledTableCell>
                  <StyledTableCell>Org ID</StyledTableCell>
                  <StyledTableCell>Description</StyledTableCell>
                  <StyledTableCell>Rule</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody> 
                {[...Array(5)].map((_, index) => (
                  <TableRow key={index}>
                    <TableCell><Skeleton animation="wave" /></TableCell>
                    <TableCell><Skeleton animation="wave" /></TableCell>
                    <TableCell><Skeleton animation="wave" /></TableCell>
                    <TableCell><Skeleton animation="wave" variant="rectangular" width={64} height={32} sx={{ borderRadius: 1 }} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TitledCard>
      )}

      {!loadingJds && jobDescriptions.length > 0 && (
        <TitledCard title="Available Job Descriptions" disableContentPadding>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <StyledTableCell>Title</StyledTableCell>
                  {/* <StyledTableCell>Org ID</StyledTableCell> */}
                  <StyledTableCell>Description</StyledTableCell>
                  <StyledTableCell>Rule</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobDescriptions.map((jd) => (
                  <StyledTableRow key={jd.id}>
                    {/* <StyledTableCell>{jd.id}</StyledTableCell> */}
                    <StyledTableCell>{jd.job_title?.data}</StyledTableCell>
                    <StyledTableCell>{jd.position_summary?.data}</StyledTableCell>
                    
                    <StyledTableCell>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          setSelectedRuleJobId(jd.id);
                          setRuleDialogOpen(true);
                        }}>
                        Rule
                      </Button>
                    </StyledTableCell>
                  </StyledTableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TitledCard>)}

      <DocxUploadModal
        open={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        onUpload={handleFileUpload}
      />

      <RuleOverlayDialog
        open={ruleDialogOpen}
        jobId={selectedRuleJobId}
        onClose={() => setRuleDialogOpen(false)}
      />      
    </PageContainer>
  );
};

export default JobDescriptionPage;
