import React, { useEffect, useState } from 'react';
import CandidateSearch from '../components/candidate_search/CandidateSearch';
import StatusAlert, { StatusMessage } from '../components/common/StatusAlert';
import {
  getOrganizationsApi,
  getJobDescriptionsApi,
  
} from '../services/apiService';
import {  MatchResultRecord } from '../types/matchTypes';
import { Organization, JobDescription } from '../types/jobDescriptionTypes';
import { useUserSession } from '../hooks/useUserSession';
import { getCandidateMatchesApi } from '../services/apiService';
import PageContainer from '../components/common/PageContainer';
const CandidateSearchPage: React.FC = () => {
  const { user } = useUserSession();
  const [orgList, setOrgList] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [jobList, setJobList] = useState<JobDescription[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | ''>('');
  const [manualDescription, setManualDescription] = useState('');
  const [results, setResults] = useState<MatchResultRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<StatusMessage | null>(null);

  useEffect(() => {
    const loadOrganizations = async () => {
      const response = await getOrganizationsApi();
      const orgs = response.data;
      console.debug('ORGANIZATION -',orgs);
      setOrgList(orgs.organizations);
      if (orgs.organizations.length > 0) {
        setSelectedOrgId(orgs.organizations[0].id);
      }
    };
    loadOrganizations();
  }, []);

  useEffect(() => {
    const loadJobs = async () => {
      if (selectedOrgId) {
        const response = await getJobDescriptionsApi(selectedOrgId);
        setJobList(response.data);
      }
    };
    loadJobs();
  }, [selectedOrgId]);

  const handleSearch = async () => {
    if (!selectedOrgId || !selectedJobId) return;
    setLoading(true);
    setMessage(null); // Clear previous messages
    setResults([]);   // Clear previous results
    try {
      const response = await getCandidateMatchesApi(selectedOrgId, String(selectedJobId));
      const matches = response.matchResults || [];
      setResults(matches);
      if (matches.length > 0) {
        const plural = matches.length > 1 ? 's' : '';
        setMessage({ type: 'success', text: `Found ${matches.length} matching candidate${plural}.` });
      } else {
        setMessage({ type: 'info', text: 'No matching candidates found for the selected job.' });
      }
    } catch (error) {
      console.error('Search error:', error);
      setMessage({ type: 'error', text: 'An error occurred during the search. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    //setResults([]);
    setMessage(null);
  };

  return (
    <PageContainer>
      <StatusAlert
        message={message}
        loading={loading}
        onClose={handleClear}
      />
      <CandidateSearch
        orgList={orgList}
        selectedOrgId={selectedOrgId}
        setSelectedOrgId={setSelectedOrgId}
        jobList={jobList}
        selectedJobId={selectedJobId}
        setSelectedJobId={setSelectedJobId}
        manualDescription={manualDescription}
        setManualDescription={setManualDescription}
        onSearch={handleSearch}
        results={results}
        loading={loading}
      />
    </PageContainer>
  );
};

export default CandidateSearchPage;
