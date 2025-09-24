// src/layouts/Footer.tsx
import React from 'react';
import { Box, Typography, Container } from '@mui/material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        p: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.background.paper,
        borderTop: '1px solid',
        borderColor: (theme) => theme.palette.divider,
      }}
    >
      <Container maxWidth="lg" sx={{ textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {'Copyright © TalentFlow AI '}
          {new Date().getFullYear()}
          {'.'}
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;