// src/pages/LoginPage.tsx
// import React, { useEffect } from 'react';
import React, { useState, useEffect } from 'react';

import { useNavigate } from 'react-router-dom';
import LoginScreen from '../components/LoginScreen';
import { useAuth } from '../hooks/useAuth';
import { LoginResponseData } from '../types/authTypes';
import { Container, CssBaseline, Grid, Link, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom'; // Import RouterLink

interface LoginPageProps {
  onAppLoginSuccess: (data: { user: LoginResponseData['user']; menuItems: LoginResponseData['menuItems']; }) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onAppLoginSuccess }) => {
  const navigate = useNavigate();
  // Get menuItems from context, too.
  const { setAppUserData, isAuthenticated, menuItems } = useAuth(); 

  const handleLocalLoginSuccess = (loginResponseData: LoginResponseData) => {
       // >>>>>>> CRITICAL DEBUG LOG HERE <<<<<<<
    console.log("LoginPage: handleLocalLoginSuccess received loginResponseData:", loginResponseData);
    console.log("LoginPage: loginResponseData.menuItems length:", loginResponseData.menuItems?.length);
    // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    setAppUserData({ user: loginResponseData.user, menuItems: loginResponseData.menuItems }); 
    console.log("LoginPage: handleLocalLoginSuccess called. setAppUserData triggered.");
    // Navigation will be handled by useEffect below.
  };

  // The navigation logic should trigger ONLY when isAuthenticated is true AND menuItems are loaded.
  useEffect(() => {
    console.log("LoginPage useEffect: isAuthenticated:", isAuthenticated, "menuItems length:", menuItems.length);
    if (isAuthenticated && menuItems.length > 0) { // <<<<< CRITICAL: Check menuItems length
      console.log("LoginPage: isAuthenticated is true AND menuItems loaded, navigating to dashboard.");
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, menuItems.length, navigate]); // Depend on menuItems.length now


  return (
    // <LoginScreen onLoginSuccess={handleLocalLoginSuccess} />

        
    <Container component="main">
      <CssBaseline />
      <LoginScreen onLoginSuccess={handleLocalLoginSuccess} />
      <Grid container justifyContent="flex-end" sx={{ mt: 2 }}>
        <Grid item>
          <Link component={RouterLink} to="/register" variant="body2">
            Don't have an account? Register

          </Link>
        </Grid>
      </Grid>
    </Container>
  );
  
};

export default LoginPage;