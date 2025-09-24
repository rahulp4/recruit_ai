// import React, { useState, useEffect } from 'react';
import React, { useState, useEffect, useRef } from 'react'; // Added import for useRef

import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Typography,
  Table,
  TableBody,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  CircularProgress,
  Chip,
  styled, // Ensure styled is imported

} from '@mui/material';
import TableCell, { tableCellClasses } from '@mui/material/TableCell';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import RefreshIcon from '@mui/icons-material/Refresh';
import TitledCard from '../common/TitledCard';
import StatusAlert, { StatusMessage } from '../common/StatusAlert';
import { getOrganizationsApi, getJobDescriptionsApi, bulkUploadResumesApi, getBulkUploadListApi, BulkUploadHistoryItem } from '../../services/apiService';
import { Organization, JobDescription } from '../../types/jobDescriptionTypes';

const VisuallyHiddenInput = styled('input')({
 
});

// Define styled components within the component
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

interface ProcessingFile {
  id: string;
  name: string;
  status: 'Processing' | 'Completed' | 'Failed';
  message?: string;
}

const BulkUploadForm: React.FC = () => {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [processingFiles, setProcessingFiles] = useState<ProcessingFile[]>([]);
  const [message, setMessage] = useState<StatusMessage | null>(null);
  const [loadingOrgs, setLoadingOrgs] = useState(true);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchOrgs = async () => {
      try {
        const response = await getOrganizationsApi();
        setOrganizations(response.data.organizations || []);
      } catch (error) {
        setMessage({ type: 'error', text: 'Failed to load organizations.' });
      } finally {
        setLoadingOrgs(false);
      }
    };
    fetchOrgs();
  }, []);

  useEffect(() => {
    if (!selectedOrgId) {
      setJobs([]);
      setSelectedJobId('');
      setProcessingFiles([]); // Clear history when org is deselected
      return;
    }
    const fetchJobs = async () => {
      setLoadingJobs(true);
      try {
        const response = await getJobDescriptionsApi(selectedOrgId);
        setJobs(response.data || []);
      } catch (error) {
        setMessage({ type: 'error', text: 'Failed to load jobs for the selected organization.' });
      } finally {
        setLoadingJobs(false);
      }
    };
    fetchJobs();
  }, [selectedOrgId]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!selectedOrgId || !selectedJobId) {
        setProcessingFiles([]);
        return;
      }
      setLoadingHistory(true);
      try {
        const response = await getBulkUploadListApi(selectedOrgId, selectedJobId, startDate, endDate);
        const history = response.data?.upload_history || [];

        // Helper to map API status strings to our component's status type
        const mapApiStatus = (apiStatus: string): ProcessingFile['status'] => {
          const lowerStatus = apiStatus.toLowerCase();
          if (lowerStatus === 'completed') return 'Completed';
          if (lowerStatus === 'failed') return 'Failed';
          // Default to 'Processing' for 'processing' or any other unknown statuses
          return 'Processing';
        };

        const historyFiles: ProcessingFile[] = history.map((item: BulkUploadHistoryItem) => ({
          id: item.upload_id,
          name: item.filename,
          status: mapApiStatus(item.status),
          message: `Uploaded: ${new Date(item.created_at).toLocaleString()}`,
        }));
        setProcessingFiles(historyFiles);
      } catch (error) {
        console.error('Failed to fetch upload history:', error);
        setMessage({ type: 'error', text: 'Failed to load upload history.' });
        setProcessingFiles([]); // Clear on error
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, [selectedOrgId, selectedJobId, startDate, endDate, refreshTrigger]); // Re-fetch when job, dates, or refresh trigger changes

 const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedOrgId || !selectedJobId) {
      setMessage({ type: 'error', text: 'Please select an Organization and Job ID before uploading.' });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
 if (!event.target.files || event.target.files.length === 0) {
      return;
    }
    const file = event.target.files[0];
    if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
      setMessage({ type: 'error', text: 'Invalid file type. Please upload a .zip file.' });
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    try {
      setIsUploading(true);
      setMessage(null);
      const response = await bulkUploadResumesApi(selectedOrgId, selectedJobId, file, file.name);
      
      // The backend returns a status of 'processing' to indicate it has accepted the file.
      // This should be treated as a success on the frontend.
      if (response.data && response.data.status === 'processing') {
        const newFileEntry: ProcessingFile = {
          id: response.data.upload_id, // Use the unique ID from the backend
          name: response.data.filename,
          status: 'Processing', // The file is already being processed
          message: 'Awaiting final status...',
        };

        setProcessingFiles(prev => [newFileEntry, ...prev]);
        setMessage({ type: 'success', text: `Successfully uploaded ${file.name}. It is now being processed.` });

        // The timer for simulating status changes has been removed as requested.
        // To get real-time updates, a polling mechanism would be needed.
      } else {
        setMessage({ type: 'error', text: response.data.message || 'Upload failed. The server did not accept the file.' });
      }
    } catch (error) {
      console.error('Bulk upload error:', error);
      setMessage({ type: 'error', text: 'An error occurred during the upload. Please try again.' });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <StatusAlert message={message} onClose={() => setMessage(null)}  />
      <TitledCard title="Bulk Description Upload">
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <FormControl fullWidth disabled={loadingOrgs}>
              <InputLabel id="org-select-label">Organization</InputLabel>
              <Select
                labelId="org-select-label"
                value={selectedOrgId}
                label="Organization"
                onChange={(e) => setSelectedOrgId(e.target.value as string)}
              >
                {organizations.map(org => <MenuItem key={org.id} value={org.id}>{org.name}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth disabled={!selectedOrgId || loadingJobs}>
              <InputLabel id="job-select-label">Job ID</InputLabel>
              <Select
                labelId="job-select-label"
                value={selectedJobId}
                label="Job ID"
                onChange={(e) => setSelectedJobId(e.target.value as string)}
              >
                {jobs.map(job => <MenuItem key={job.id} value={job.id}>{job.id} - {job.job_title?.data}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="Start Date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              disabled={!selectedJobId}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              label="End Date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
              disabled={!selectedJobId}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              component="label"
              role={undefined}
              variant="contained"
              tabIndex={-1}
                startIcon={isUploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
              disabled={!selectedOrgId || !selectedJobId || isUploading }

            >
              {isUploading ? 'Uploading...' : 'Upload Zip File'}
              <VisuallyHiddenInput ref={fileInputRef} type="file" onChange={handleFileChange} accept=".zip,application/zip" />

            </Button>
          </Grid>
        </Grid>
      </TitledCard>

      {selectedJobId && (
        <TitledCard
          title={
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap' }}>
              <Typography variant="h6" component="div">
                Upload History
              </Typography>
              <Button
                size="small"
                onClick={() => setRefreshTrigger(c => c + 1)}
                disabled={loadingHistory}
                startIcon={loadingHistory ? <CircularProgress size={16} color="inherit" /> : <RefreshIcon />}
              >
                Refresh
              </Button>
            </Box>
          }
          disableContentPadding>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <StyledTableCell>File Name</StyledTableCell>
                  <StyledTableCell>Status</StyledTableCell>
                  <StyledTableCell>Details</StyledTableCell>
                  <StyledTableCell align="right">Actions</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loadingHistory ? (
                  <TableRow>
                    <StyledTableCell colSpan={4} align="center">
                      <CircularProgress />
                      <Typography >Loading History...</Typography>
                    </StyledTableCell>
                  </TableRow>
                ) : processingFiles.length > 0 ? ( 
                  processingFiles.map((file) => (
                    <StyledTableRow key={file.id}>
                      <StyledTableCell>{file.name}</StyledTableCell>
                      <StyledTableCell>
                        <Chip
                          label={file.status}
                          color={file.status === 'Completed' ? 'success' : file.status === 'Failed' ? 'error' : 'info'}
                          variant="outlined"
                        />
                      </StyledTableCell>
                      <StyledTableCell >{file.message}</StyledTableCell>
                      <StyledTableCell align="right">
                        <Button
                          variant="outlined"
                          size="small"
                          disabled={file.status !== 'Completed'}
                          onClick={() => {
                            const searchParams = new URLSearchParams();
                            searchParams.set('organization_id', selectedOrgId);
                            searchParams.set('job_id', selectedJobId);
                            searchParams.set('upload_id', file.id);

                            navigate(`/candidate-search?${searchParams.toString()}`);
                          }}
                        >
                          View
                        </Button>
                      </StyledTableCell>
                    </StyledTableRow>
                  ))
                ) : (
                  <TableRow>
                    <StyledTableCell colSpan={4} align="center">
                      No upload history found for this job.
                    </StyledTableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </TitledCard>
      )}
    </>
  );
};

export default BulkUploadForm;