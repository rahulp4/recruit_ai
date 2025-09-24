import React, { useEffect, useState } from 'react';
import {
  Dialog,
  Paper,
  DialogTitle,
  DialogContent,
  Typography,
  CircularProgress,
  IconButton,
  Stack,
  Divider,
  Box,
  Chip,
  Grid,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { getJobRuleByIdApi } from '../../services/apiService';
import TitledCard from './TitledCard';

interface RuleOverlayDialogProps {
  open: boolean;
  jobId: string | null;
  onClose: () => void;
}

interface RuleField {
  data: string | string[];
  matchreq: string;
  profiledatasource: string[];
  sourcecondition: string | null;
  type: string;
  weightage: number;
  fromsource?: string | null;
}

// const renderRuleSection = (label: string, field: RuleField) => (
//   <Box key={label} sx={{ mb: 3 }}>
//     <Typography variant="h6">{label}</Typography>
//     <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
//       MatchReq: <strong>{field.matchreq}</strong> | Type: <strong>{field.type}</strong> | Weightage: <strong>{field.weightage}</strong>
//       {field.sourcecondition && <> | Source Condition: <strong>{field.sourcecondition}</strong></>}
//     </Typography>
//     <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Data:</Typography>
//     {Array.isArray(field.data) ? (
//       <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
//         {field.data.map((item, idx) => (
//           <Chip label={item} key={idx} size="small" />
//         ))}
//       </Box>
//     ) : (
//       <Typography sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>{field.data}</Typography>
//     )}
//     <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>Profile Data Source:</Typography>
//     <ul style={{ marginTop: 0 }}>
//       {field.profiledatasource.map((src, idx) => (
//         <li key={idx}>{src}</li>
//       ))}
//     </ul>
//   </Box>
// );

const RuleSectionCard: React.FC<{ label: string; field: RuleField }> = ({ label, field }) => {
  const capitalizedLabel = label.charAt(0).toUpperCase() + label.slice(1).replace(/_/g, ' ');

  return (
    <Paper elevation={1} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 1, bgcolor: '#EBF3FE' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
          {capitalizedLabel}
        </Typography>
      </Box>
      <Divider />
      <Box sx={{ p: 1.5, flexGrow: 1 }}>
        <Stack spacing={1.5}>
          <Box>
            <Typography variant="caption" color="textSecondary">
              Match: <strong>{field.matchreq}</strong> | Type: <strong>{field.type}</strong> | Weight: <strong>{field.weightage}</strong>
              {field.sourcecondition && <> | Condition: <strong>{field.sourcecondition}</strong></>}
            </Typography>
          </Box>
          <Divider />
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>Data:</Typography>
            {Array.isArray(field.data) ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {field.data.map((item, idx) => <Chip label={item} key={idx} size="small" />)}
              </Box>
            ) : (
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', bgcolor: 'action.hover', p: 1, borderRadius: 1 }}>{field.data}</Typography>
            )}
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>Profile Data Source:</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {field.profiledatasource.map((src, idx) => <Chip label={src} key={idx} size="small" variant="outlined" />)}
            </Box>
          </Box>
        </Stack>
      </Box>
    </Paper>
  );
};

const RuleOverlayDialog: React.FC<RuleOverlayDialogProps> = ({ open, jobId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [ruleData, setRuleData] = useState<any | null>(null);

  useEffect(() => {
    const fetchRule = async () => {
      if (!jobId || !open) return;
      setLoading(true);
      try {
        const response = await getJobRuleByIdApi(jobId);
        setRuleData(response.data);
      } catch (err) {
        setRuleData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchRule();
  }, [jobId, open]);

  const getGeneralRuleFields = () => {
    if (!ruleData) return [];

    return Object.entries(ruleData)
      .filter(
        ([key, value]) =>
          typeof value === 'object' &&
          value !== null &&
          'data' in value &&
          key !== 'keywordmatch'
      ) as [string, RuleField][];
  };

  const getKeywordMatchFields = () => {
    if (!ruleData || !ruleData.keywordmatch) return [];

    return Object.entries(ruleData.keywordmatch).filter(
      ([, value]) => value !== null
    ) as [string, RuleField][];
  };

  return (
    <Dialog open={open} fullScreen onClose={onClose}>
      <DialogTitle sx={{ bgcolor: '#5D87FF', color: 'white', py: 1.5 }}>
        Rule Details
        <IconButton
          onClick={onClose}
          sx={{ position: 'absolute', right: 8, top: 8, color: 'white' }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ bgcolor: 'background.default', p: { xs: 1, sm: 2 } }}>
        {loading ? (
          // <CircularProgress />
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <CircularProgress />
          </Box>          
        ) : ruleData ? (
          // <Stack spacing={2}>
          //   <Typography variant="h5">General Matching Rules</Typography>
          //   <Divider />
          //   {getGeneralRuleFields().map(([label, field]) => renderRuleSection(label, field))}

          //   <Typography variant="h5" sx={{ mt: 4 }}>Keyword Match Rules</Typography>
          //   <Divider />
          //   {getKeywordMatchFields().map(([label, field]) => renderRuleSection(label, field))}
           <Stack spacing={3}>
            {getGeneralRuleFields().length > 0 && (
              <TitledCard title="General Matching Rules">
                <Grid container spacing={1.5}>
                  {getGeneralRuleFields().map(([label, field]) => (
                    <Grid item xs={12} sm={6} md={4} key={label}>
                      <RuleSectionCard label={label} field={field} />
                    </Grid>
                  ))}
                </Grid>
              </TitledCard>
            )}
            {getKeywordMatchFields().length > 0 && (
              <TitledCard title="Keyword Match Rules">
                <Grid container spacing={1.5}>
                  {getKeywordMatchFields().map(([label, field]) => (
                    <Grid item xs={12} sm={6} md={4} key={label}>
                      <RuleSectionCard label={label} field={field} />
                    </Grid>
                  ))}
                </Grid>
              </TitledCard>
            )}
          </Stack>
        ) : (
          <Typography color="error">Failed to load rule data.</Typography>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default RuleOverlayDialog;
