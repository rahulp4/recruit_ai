import React, { useState } from 'react';
import {
  Box, Grid, TextField, Button,
  FormControl, InputLabel, Select, MenuItem, Table, TableBody, Skeleton, TableSortLabel,
  TableContainer, TableHead, TableRow
} from '@mui/material';
import { styled } from '@mui/material/styles';
import TableCell, { tableCellClasses } from '@mui/material/TableCell';
import {  MatchResultRecord, MatchResultResponse } from '../../types/matchTypes';
import { Organization, JobDescription } from '../../types/jobDescriptionTypes';
import MatchResultDialog from '../dialogs/MatchResultDialog';
import TitledCard from '../common/TitledCard';

interface MatchResultDetail {
  field: string;
  req_data: any;
}

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

interface Props {
  orgList: Organization[];
  selectedOrgId: string;
  setSelectedOrgId: (orgId: string) => void;
  jobList: JobDescription[];
  selectedJobId: number | '';
  setSelectedJobId: (jobId: number | '') => void;
  manualDescription: string;
  setManualDescription: (desc: string) => void;
  onSearch: () => void;
  results: MatchResultRecord[];
  loading: boolean;
}

const CandidateSearch: React.FC<Props> = ({
  orgList, selectedOrgId, setSelectedOrgId,
  jobList, selectedJobId, setSelectedJobId,
  manualDescription, setManualDescription,
  onSearch, results, loading
}) => {
  const [selectedMatch, setSelectedMatch] = useState<MatchResultResponse | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');
  const [orderBy, setOrderBy] = useState<keyof MatchResultRecord | 'jobTitle'>('overallScore');

  const handleViewDetails = (matchData: MatchResultResponse | null) => {
    if (matchData) {
      setSelectedMatch(matchData);
      setIsDialogOpen(true);
    }
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setSelectedMatch(null);
  };

  const handleRequestSort = (property: keyof MatchResultRecord | 'jobTitle') => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedResults = React.useMemo(() => {
    if (!results || results.length === 0) return [];

    const getJobTitle = (row: MatchResultRecord) =>
      row.matchResultsJson?.results?.find((r: MatchResultDetail) => r.field === 'job_title')?.req_data || '';

    return [...results].sort((a, b) => {
      let compareA: any;
      let compareB: any;

      if (orderBy === 'jobTitle') {
        compareA = getJobTitle(a).toLowerCase();
        compareB = getJobTitle(b).toLowerCase();
      } else {
        compareA = a[orderBy as keyof MatchResultRecord];
        compareB = b[orderBy as keyof MatchResultRecord];
      }

      if (compareB < compareA) {
        return order === 'asc' ? 1 : -1;
      }
      if (compareB > compareA) {
        return order === 'asc' ? -1 : 1;
      }
      return 0;
    });
  }, [results, order, orderBy]);


  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TitledCard title="🔎 Candidate Search">
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel id="org-label">Organization</InputLabel>
              <Select
                labelId="org-label"
                value={selectedOrgId}
                onChange={(e) => setSelectedOrgId(e.target.value)}
                label="Organization"
              >
                {orgList.map((org) => (
                  <MenuItem key={org.id} value={org.id}>{org.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={4}>
            <FormControl fullWidth>
              <InputLabel id="job-label">Job ID</InputLabel>
              <Select
                labelId="job-label"
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
                label="Job ID"
                disabled={!selectedOrgId}
              >
                {jobList.map((job) => (
                  // <MenuItem key={job.id} value={job.id}>{job.id} - {job.title}</MenuItem>
                <MenuItem key={job.id} value={job.id}>
    {`${job.id} - ${job.job_title?.data ?? ''}`}
  </MenuItem>
    
                  // <MenuItem key={job.id} value={job.id}>
                  //     {`${job.id} - ${job.job_title}`}
                  // </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              label="Enter Job Description for Search (Optional)"
              fullWidth
              multiline
              minRows={2}
              value={manualDescription}
              onChange={(e) => setManualDescription(e.target.value)}
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={onSearch}
              disabled={loading || !selectedOrgId || !selectedJobId}
            >
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </Grid>
        </Grid>
      </TitledCard>

      {loading && (
        <TitledCard title="📄 Searching for Candidates..." disableContentPadding>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <StyledTableCell>Candidate Name</StyledTableCell>
                  <StyledTableCell>Profile ID</StyledTableCell>
                  <StyledTableCell align="right">Overall Score</StyledTableCell>
                  <StyledTableCell>Job Title</StyledTableCell>
                  <StyledTableCell>Actions</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[...Array(5)].map((_, index) => (
                  <TableRow key={index}>
                    <TableCell><Skeleton animation="wave" /></TableCell>
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

      {!loading && results.length > 0 && (
        <TitledCard title="📄 Search Results" disableContentPadding>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <StyledTableCell sortDirection={orderBy === 'candidateName' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'candidateName'}
                      direction={orderBy === 'candidateName' ? order : 'asc'}
                      onClick={() => handleRequestSort('candidateName')}
                    >
                      Candidate Name
                    </TableSortLabel>
                  </StyledTableCell>
                  <StyledTableCell sortDirection={orderBy === 'profileId' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'profileId'}
                      direction={orderBy === 'profileId' ? order : 'asc'}
                      onClick={() => handleRequestSort('profileId')}
                    >
                      Profile ID
                    </TableSortLabel>
                  </StyledTableCell>
                  <StyledTableCell align="right" sortDirection={orderBy === 'overallScore' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'overallScore'}
                      direction={orderBy === 'overallScore' ? order : 'asc'}
                      onClick={() => handleRequestSort('overallScore')}
                    >
                      Overall Score
                    </TableSortLabel>
                  </StyledTableCell>
                  <StyledTableCell sortDirection={orderBy === 'jobTitle' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'jobTitle'}
                      direction={orderBy === 'jobTitle' ? order : 'asc'}
                      onClick={() => handleRequestSort('jobTitle')}
                    >
                      Job Title
                    </TableSortLabel>
                  </StyledTableCell>
                  <StyledTableCell>Actions</StyledTableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sortedResults.map((row) => {
                  const jobTitle = row.matchResultsJson?.results?.find((r: MatchResultDetail) => r.field === 'job_title')?.req_data || 'N/A';
                  return (
                    <StyledTableRow key={row.id} hover>
                      <StyledTableCell>{row.candidateName}</StyledTableCell>
                      <StyledTableCell>{row.profileId}</StyledTableCell>
                      <StyledTableCell align="right">{row.overallScore.toFixed(2)}</StyledTableCell>
                      <StyledTableCell>{jobTitle}</StyledTableCell>
                      <StyledTableCell>
                        <Button
                          variant="outlined"
                          onClick={() => handleViewDetails(row.matchResultsJson)}
                        >
                          View
                        </Button>
                      </StyledTableCell>
                    </StyledTableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </TitledCard>
      )}
      {selectedMatch && (
        <MatchResultDialog
          open={isDialogOpen}
          onClose={handleCloseDialog}
          matchResponse={selectedMatch}
        />
      )}
    </Box>
  );
};

export default CandidateSearch;
