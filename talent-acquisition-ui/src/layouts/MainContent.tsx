// src/layouts/MainContent.tsx
import React from 'react';
import { Box, Container } from '@mui/material'; // Ensure Container is imported

interface MainContentProps {
  children: React.ReactNode;
}

const MainContent: React.FC<MainContentProps> = ({ children }) => {
  return (
    <Box
      component="main" // Semantic main tag
      sx={{
        flexGrow: 1, // Allows content to take up available vertical space
        // py: 2.5, // Vertical padding (can be adjusted)
        // px: { xs: 2, sm: 2.5 } // Horizontal padding (can be adjusted)
        // Padding is now handled by the PageContainer component inside each page        
      }}
    >
      {/*
        Option 1: Full width container (no max width, no internal gutters from container)
        This will make your DashboardPage content (the Grid) span the full width
        available in this MainContent Box, respecting only the px above.
      */}
      <Container maxWidth={false} disableGutters>
        {children}
      </Container>

      {/*
        Option 2: If you still want a max-width but less aggressive centering,
        you could try a smaller maxWidth like "lg" or adjust px on the Box above.
        <Container maxWidth="lg">
          {children}
        </Container>
      */}
    </Box>
  );
};

export default MainContent;