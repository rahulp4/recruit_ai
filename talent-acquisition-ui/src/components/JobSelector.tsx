import React from 'react';
import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { JobDesc } from '../types/candidateSearchTypes';

interface JobSelectorProps {
  jobList: JobDesc[];
  selectedJobId: string;
  onChange: (jobId: string) => void;
}

const JobSelector: React.FC<JobSelectorProps> = ({ jobList, selectedJobId, onChange }) => (
  <FormControl fullWidth margin="normal" size="small">
    <InputLabel id="job-selector-label">Job</InputLabel>
    <Select
      labelId="job-selector-label"
      value={selectedJobId}
      label="Job"
      onChange={(e) => onChange(e.target.value)}
    >
      <MenuItem value="">
        <em>None</em>
      </MenuItem>
      {jobList.map((job) => (
        <MenuItem key={job.id} value={job.id}>
          {job.id} – {job.title}
        </MenuItem>
      ))}
    </Select>
  </FormControl>
);

export default JobSelector;
