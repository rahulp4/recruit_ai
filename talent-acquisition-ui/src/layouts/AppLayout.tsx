// src/layouts/AppLayout.tsx
import React, { useState, useEffect } from 'react';
import { Box, CssBaseline, useTheme, useMediaQuery, Toolbar } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import Footer from './Footer';

const drawerWidth = 220; // Full width of the open sidebar

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  console.log("AppLayout - sidebarOpen:", sidebarOpen, "isMobile:", isMobile);

  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  const handleToggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // Calculate collapsed width string based on theme spacing for sm screens and up
  const collapsedDrawerWidth = isMobile ? '0px' : `calc(${theme.spacing(7)} + 1px)`; // Approx 57px-65px
                                                                                    // For sm screens, it's theme.spacing(8) usually
  const smCollapsedDrawerWidth = `calc(${theme.spacing(8)} + 1px)`; // Used for Header adjustment consistency


  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <CssBaseline />
      <Header
        sidebarOpen={sidebarOpen}
        onToggleSidebar={handleToggleSidebar}
        drawerWidth={drawerWidth}
        // Pass the correct collapsed width for sm screens to the Header
        collapsedDrawerWidth={smCollapsedDrawerWidth} 
      />
      <Sidebar
        sidebarOpen={sidebarOpen}
        drawerWidth={drawerWidth}
        onToggleSidebar={handleToggleSidebar}
      />

      {/* Main Content Wrapper */}
      <Box
        component="div"
        sx={{
          flexGrow: 1, // This will make it take the remaining horizontal space
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.palette.background.default, // Your theme's default background
          // No explicit marginLeft here, as the persistent Drawer should push it.
          // Width will be determined by flexGrow.
          // The transition of this Box might not be needed if the Sidebar's transition handles the reflow.
          // However, if you want content to also animate its width smoothly, you might need it.
          // For now, let's rely on the Sidebar's own transition to cause the reflow.
          transition: theme.transitions.create('width', { // Only transition width if it changes
            easing: theme.transitions.easing.sharp,
            duration: sidebarOpen 
                ? theme.transitions.duration.enteringScreen 
                : theme.transitions.duration.leavingScreen,
          }),
          boxSizing: 'border-box',
          // The actual width will be (parent width - sidebar width) due to flexbox
        }}
      >
        <Toolbar /> {/* Spacer for the fixed AppBar */}
        <MainContent>{children}</MainContent>
        <Footer />
      </Box>
    </Box>
  );
};

export default AppLayout;