// src/components/LoginScreen.tsx
import React, { useState } from 'react';
import {
  Box, Button, TextField, Typography,Grid ,Paper, InputAdornment, Link, CircularProgress
} from '@mui/material';
import MailOutlineIcon from '@mui/icons-material/MailOutline';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import BusinessOutlinedIcon from '@mui/icons-material/BusinessOutlined';
import useLogin from '../hooks/useLogin'; // Corrected path
import axios from 'axios'; // Import axios
import { LoginResponseData } from '../types/authTypes'; // Import LoginResponseData
import { Link as RouterLink } from 'react-router-dom'; // Import RouterLink
interface LoginScreenProps {
  onLoginSuccess: (data: LoginResponseData) => void; // This is correct
}

function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const {
    organizationId, setEmail, setOrganizationId, setPassword, email, password,
    errorMessage, isLoading, handleLogin,
  } = useLogin();

  const handleSubmit = async (e: React.FormEvent) => {
    const loginResult = await handleLogin(e); // This now returns LoginResponseData | null
    
    if (loginResult) { // If loginResult is not null (meaning success)
      onLoginSuccess(loginResult); // <<<<<< PASS THE REAL loginResult data
    }
  };

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
      <Paper elevation={3} sx={{ width: '100%', maxWidth: '960px', display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}>
        {/* Left Section: Image or Branding */}
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
          <Box
            component="img"
            src="https://placehold.co/150x150/FFFFFF/4F46E5?text=YourLogo"
            alt="Company Logo"
            sx={{ mb: 3, borderRadius: '50%', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}
            onError={(e: React.SyntheticEvent<HTMLImageElement, Event>) => {
              const target = e.target as HTMLImageElement;
              target.onerror = null;
              target.src = "https://placehold.co/150x150/FFFFFF/4F46E5?text=YourLogo";
            }}
          />
          <Typography variant="h1" component="h1" gutterBottom>
            Welcome Back!
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            Streamline your talent acquisition process with ease
          </Typography>
        </Box>

        {/* Right Section: Login Form */}
        <Box
          sx={{
            flex: 1,
            p: { xs: 4, lg: 6 },
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="h2" component="h2" gutterBottom>
              Sign In
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Enter your credentials to access your account
            </Typography>
          </Box>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3, '& > :not(style)': { mb: 3 } }}>
            <TextField
              fullWidth
              id="organizationId"
              label="Organization ID"
              name="organizationId"
              type="text"
              autoComplete="organization-id"
              required
              className="appearance-none block w-full px-3 py-3 pl-10 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="Organization ID"
              value={organizationId}
              onChange={(e) => setOrganizationId(e.target.value)}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BusinessOutlinedIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="appearance-none block w-full px-3 py-3 pl-10 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <MailOutlineIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              className="appearance-none block w-full px-3 py-3 pl-10 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockOutlinedIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />

            {errorMessage && (
              <Typography color="error" variant="body2" align="center" sx={{ mt: -4, mb: 2 }}>
                {errorMessage}
              </Typography>
            )}

            <div>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ mt: 2 }}
                disabled={isLoading}
              >
                {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
              </Button>
            </div>
          </Box>

          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">

 <Link component={RouterLink} to="/register" variant="body2">
            Don't have an account? Register

          </Link>
            </Typography>
          </Box>
          {/* <Box sx={{ mt: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}


              <Link href="#" color="primary" underline="hover">
                Contact Support
              </Link>
            </Typography>
          </Box> */}
        </Box>
      </Paper>
    </Box>
  );
}

export default LoginScreen;