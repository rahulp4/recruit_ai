// src/components/dashboard/DashboardWelcome.tsx
import React from 'react';
import { Typography, Box } from '@mui/material';
import { useAuth } from '../../hooks/useAuth'; // To get user's name/email

const DashboardWelcome: React.FC = () => {
  //const { user } = useAuth();
  const { appUser, firebaseUser } = useAuth(); // <<<<< Use appUser or firebaseUser

  // Use a more generic placeholder if email is not available or user is not loaded yet
//  const displayName = user?.email || (user?.displayName || 'Valued User');
  const displayName = appUser?.email || firebaseUser?.displayName || firebaseUser?.email || 'Valued User';


  return (
    // This Box provides its own spacing if needed, now that it's not in a Paper component
    // The parent Box in DashboardPage already provides mb: 3, so direct children might not need more.
    // Adjust sx here if further specific styling for the welcome message block is needed.
    <Box sx={{ py: 1 }}> 
      <Typography variant="h4" component="h1" gutterBottom fontWeight="700">
        Welcome back, {displayName}!
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Here's a quick overview of your talent acquisition activities. Let's find some great candidates!
      </Typography>
    </Box>
  );
};

export default DashboardWelcome;