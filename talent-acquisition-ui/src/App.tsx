/*
const firebaseConfig = {
  apiKey: "AIzaSyB6dG7sEKtI-NQO_k3-AZSSLXq-nJMzSEk",
  authDomain: "profileauth-90a2f.firebaseapp.com",
  projectId: "profileauth-90a2f",
  storageBucket: "profileauth-90a2f.firebasestorage.app",
  messagingSenderId: "449144548740",
  appId: "1:449144548740:web:62f4ed418007908ec081d1"
};

*/
// src/App.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { Box, CircularProgress, Typography } from '@mui/material';

import theme from './theme';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ResumeUploadPage from './pages/ResumeUploadPage';
import AnalyseResumePage from './pages/AnalyseResumePage';
import AppLayout from './layouts/AppLayout';
import JobDescriptionPage from './pages/JobDescriptionPage'; // <<<<< NEW IMPORT
import BulkUploadPage from './pages/ BulkUploadForm';

import CandidateSearchPage from './pages/CandidateSearchPage';
import { AuthProvider, useAuth } from './hooks/useAuth'; // Ensure .tsx is explicit if needed by your setup
import CreateUserPage from './pages/CreateUserPage';
import RegisterPage from './pages/RegisterPage'; // You'll need to create and import this

// Firebase Config (Keep yours)

const firebaseConfig = {
  apiKey: "AIzaSyB6dG7sEKtI-NQO_k3-AZSSLXq-nJMzSEk",
  authDomain: "profileauth-90a2f.firebaseapp.com",
  projectId: "profileauth-90a2f",
  storageBucket: "profileauth-90a2f.firebasestorage.app",
  messagingSenderId: "449144548740",
  appId: "1:449144548740:web:62f4ed418007908ec081d1"
};
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app); // Export the auth instance

// Moved AppContent's logic into App component, and wrapped it all in AuthProvider
function App() {
  return (
    <ThemeProvider theme={theme}> {/* ThemeProvider typically wraps the entire app */}
      <CssBaseline /> {/* CssBaseline also typically wraps the entire app */}
      <Router> {/* Router should be outside AuthProvider if you want to handle auth redirection at root */}
        <AuthProvider> {/* <<<<< AuthProvider now wraps the Routes and all components that use useAuth */}
          <AppRoutes /> {/* A new component to contain the routes */}
        </AuthProvider>
      </Router>
    </ThemeProvider>
  );
}

// New component to contain the application's routes and use AuthContext
function AppRoutes() {
  const { isAuthenticated, isLoadingAuth } = useAuth(); // <<<<< useAuth() is now called INSIDE AuthProvider's children

  // This function will still be passed to LoginPage
  const handleAppLoginSuccess = useCallback(() => {
    console.log("AppRoutes: Login success signaled. AuthProvider handles state.");
  }, []);

  if (isLoadingAuth) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress /> <Typography variant="h6" sx={{ ml: 2 }}>Initializing App...</Typography>
      </Box>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage onAppLoginSuccess={handleAppLoginSuccess} />}
      />
      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={isAuthenticated ? <AppLayout><DashboardPage /></AppLayout> : <Navigate to="/login" replace />}
      />
      <Route
        path="/upload-resume"
        element={isAuthenticated ? <AppLayout><ResumeUploadPage /></AppLayout> : <Navigate to="/login" replace />}
      />
      <Route
        path="/analyse-resume"
        element={isAuthenticated ? <AppLayout><AnalyseResumePage /></AppLayout> : <Navigate to="/login" replace />}
      />
     <Route
        path="/jobs" // <<<<< NEW ROUTE
        element={isAuthenticated ? <AppLayout><JobDescriptionPage /></AppLayout> : <Navigate to="/login" replace />}
      />

   
     <Route
        path="/candidate-search" // <<<<< NEW ROUTE
        element={isAuthenticated ? <AppLayout><CandidateSearchPage /></AppLayout> : <Navigate to="/login" replace />}
      />

      {/* <Route path="/users/create" element={<AppLayout><CreateUserPage /></AppLayout>} /> */}
          <Route path="/register" element={<RegisterPage />} />

  <Route
        path="/bulk-upload"
        element={isAuthenticated ? <AppLayout><BulkUploadPage /></AppLayout> : <Navigate to="/login" replace />}
      />

      {/* Root path redirect */}
      <Route
        path="/"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />}
      />
   
      {/* Fallback */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
      />
    </Routes>

    
  );
}

export default App;