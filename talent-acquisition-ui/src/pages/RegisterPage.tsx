// src/pages/RegisterPage.tsx
import React from 'react';
import { Box, Paper, Typography, CssBaseline } from '@mui/material';
import RegisterForm from '../components/auth/RegisterForm';

const RegisterPage: React.FC = () => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: 'background.default',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <CssBaseline />
      <Paper elevation={3} sx={{ width: '100%', maxWidth: '960px', display: 'flex', flexDirection: { xs: 'column', md: 'row' }, overflow: 'hidden' }}>
        {/* Left Section: Branding */}
        <Box
          sx={{
            flex: 1,
            background: 'linear-gradient(to bottom right, #4F46E5, #8B5CF6)',
            p: { xs: 4, md: 8 },
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            textAlign: 'center',
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 'bold' }}>
            Join Our Platform
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.9 }}>
            Unlock your potential in talent acquisition.
          </Typography>
        </Box>

        {/* Right Section: Register Form */}
        <Box
          sx={{
            flex: 1,
            p: { xs: 3, sm: 4, lg: 6 },
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}
        >
          <RegisterForm />
        </Box>
      </Paper>
    </Box>
  );
};

export default RegisterPage;