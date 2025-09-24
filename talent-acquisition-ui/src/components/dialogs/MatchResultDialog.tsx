import React from 'react';
import {
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableContainer,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  IconButton,
  Paper
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import { MatchResultResponse } from '../../types/matchTypes'; // adjust import path if needed
import CloseIcon from '@mui/icons-material/Close';
import { MatchResultResponse } from '../../types/matchTypes';
import TitledCard from '../common/TitledCard';

interface MatchResultDialogProps {
  open: boolean;
  onClose: () => void;
  matchResponse?: MatchResultResponse;
}

const MatchResultDialog: React.FC<MatchResultDialogProps> = ({
  open,
  onClose,
  matchResponse,
}) => {
    console.debug("RESULT ",matchResponse);
  if (!matchResponse || !matchResponse.results) {
    return (
      <Dialog open={open} onClose={onClose}>
        <DialogTitle>No Match Results Available</DialogTitle>
        <DialogContent>
          <Typography>Match results could not be loaded or are missing.</Typography>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    // <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
    //   <DialogTitle>Match Results</DialogTitle>
    //   <DialogContent>
    //     <Box mb={2}>
    //       <Typography variant="subtitle1">Overall Scores:</Typography>
    //       <Typography variant="body2">Weighted: {matchResponse.overall_score_weighted}%</Typography>
    //       <Typography variant="body2">Average (All): {matchResponse.overall_score_average_all}%</Typography>
    //       <Typography variant="body2">Average (Non-zero): {matchResponse.overall_score_average_non_zero}%</Typography>
    //       <Typography variant="body2">Max Score: {matchResponse.max_score}% (Field: {matchResponse.max_score_field})</Typography>
    //     </Box>
  <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth scroll="body">
      <DialogTitle sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', py: 1.5 }}>
        Match Analysis Report
        <IconButton onClick={onClose} sx={{ position: 'absolute', right: 8, top: 8, color: 'primary.contrastText' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ bgcolor: 'background.default', p: { xs: 1, sm: 2 } }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TitledCard title="Overall Score Analysis">
              <Grid container spacing={2} textAlign="center">
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Weighted Score</Typography>
                  <Typography variant="h5" fontWeight="bold">{matchResponse.overall_score_weighted?.toFixed(2) ?? 'N/A'}%</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Average (All)</Typography>
                  <Typography variant="h5" fontWeight="bold">{matchResponse.overall_score_average_all?.toFixed(2) ?? 'N/A'}%</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Average (Non-zero)</Typography>
                  <Typography variant="h5" fontWeight="bold">{matchResponse.overall_score_average_non_zero?.toFixed(2) ?? 'N/A'}%</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="caption" color="textSecondary">Max Score</Typography>
                  <Typography variant="h5" fontWeight="bold">
                    {matchResponse.max_score?.toFixed(2) ?? 'N/A'}%
                    <Typography variant="body2" component="span" color="text.secondary"> ({matchResponse.max_score_field})</Typography>
                  </Typography>
                </Grid>
              </Grid>
            </TitledCard>
          </Grid>

          <Grid item xs={12}>
            <TitledCard title="Detailed Field-by-Field Breakdown">
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {matchResponse.results.map((result, idx) => (
                  <Accordion key={idx} defaultExpanded={idx < 3} elevation={2}>
                    <AccordionSummary
                      expandIcon={<ExpandMoreIcon />}
                      sx={{
                        bgcolor: 'primary.light',
                        color: 'primary.contrastText',
                        minHeight: 48,
                        '&.Mui-expanded': { minHeight: 48 },
                        '& .MuiAccordionSummary-content': {
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        },
                      }}
                    >
                      <Typography sx={{ flexBasis: '33.33%', flexShrink: 0, fontWeight: 'bold' }}>
                        {result.field}
                      </Typography>
                      <Typography sx={{ flexBasis: '33.33%', textAlign: 'center', color: 'text.primary' }}>
                        Score: <strong>{result.score?.toFixed(2)}</strong>
                      </Typography>
                      <Typography sx={{ flexBasis: '33.33%', textAlign: 'right', color: 'text.primary' }}>
                        Confidence: <strong>{result.confidence?.toFixed(2)}</strong>
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails sx={{ bgcolor: 'background.paper', p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2"><strong>Best Source:</strong> {result.best_source_used || 'N/A'}</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                            <strong>Required Data:</strong> {Array.isArray(result.req_data) ? result.req_data.join(', ') : String(result.req_data)}
                          </Typography>
                        </Grid>
                        {result.sources_evaluated && result.sources_evaluated.length > 0 && (
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" sx={{ mt: 1, fontWeight: 'bold' }}>Sources Evaluated</Typography>
                            <TableContainer component={Paper} variant="outlined" sx={{ mt: 1 }}>
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell>Source Field</TableCell>
                                    <TableCell>Data</TableCell>
                                    <TableCell>Score</TableCell>
                                    <TableCell>Confidence</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {result.sources_evaluated.map((src, i) => (
                                    <TableRow key={i}>
                                      <TableCell>{src.source_field}</TableCell>
                                      <TableCell sx={{ maxWidth: 200, wordBreak: 'break-word' }}>
                                        {Array.isArray(src.data)
                                          ? src.data.map((d) =>
                                              Array.isArray(d) ? d.join(', ') : d
                                            ).join(' | ')
                                          : String(src.data)}
                                      </TableCell>
                                      <TableCell>{src.score?.toFixed(2)}</TableCell>
                                      <TableCell>{src.confidence?.toFixed(2)}</TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            </TableContainer>
                          </Grid>
                        )}
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </Box>
            </TitledCard>
          </Grid>
        </Grid>        
      </DialogContent>
    </Dialog>
  );
};

export default MatchResultDialog;
