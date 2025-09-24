// src/layouts/Sidebar.tsx
import React from 'react';
import { Drawer, Toolbar, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Divider, Box, Tooltip, Typography, useTheme, useMediaQuery, ListSubheader } from '@mui/material';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import PeopleOutlineOutlinedIcon from '@mui/icons-material/PeopleOutlineOutlined';
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined';
import UploadFileOutlinedIcon from '@mui/icons-material/UploadFileOutlined';
import AnalyticsOutlinedIcon from '@mui/icons-material/AnalyticsOutlined'; // <<<<< NEW ICON
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'; // <<<<< NEW ICON
import BackupTableOutlinedIcon from '@mui/icons-material/BackupTableOutlined';
// import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Box, Divider, Typography, ListSubheader } from '@mui/material';

import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';
import HelpOutlineOutlinedIcon from '@mui/icons-material/HelpOutlineOutlined';
import { NavLink, useLocation } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth'; // <<<<< IMPORT useAuth
import { BackendMenuItem } from '../types/authTypes'; // <<<<< NEW IMPORT FOR BackendMenuItem

// Helper to map Font Awesome (fa-...) icon names to Material-UI Icons
const getMuiIconComponent = (iconName: string, iconSize: 'small' | 'medium' | 'large') => {
  switch (iconName) {
    case 'fa-home': return <DashboardOutlinedIcon fontSize={iconSize} />;
    case 'fa-upload': return <UploadFileOutlinedIcon fontSize={iconSize} />;
    case 'fa-upload-bulk': return <BackupTableOutlinedIcon fontSize={iconSize} />;

    case 'fa-chart-bar': // Assuming this for analytics
    case 'fa-analytics': return <AnalyticsOutlinedIcon fontSize={iconSize} />;
    case 'fa-briefcase': // For Job Post
    case 'fa-upload-job': return <WorkOutlineOutlinedIcon fontSize={iconSize} />; // Assuming fa-upload for Job Post
    case 'fa-users': // For Candidates
    case 'fa-user-group': return <PeopleOutlineOutlinedIcon fontSize={iconSize} />;
    case 'fa-file-alt': // Assuming this for job descriptions
    case 'fa-file-contract': return <DescriptionOutlinedIcon fontSize={iconSize} />; // <<<<< NEW MAPPING       
    case 'fa-cog': return <SettingsOutlinedIcon fontSize={iconSize} />;
    case 'fa-question-circle': return <HelpOutlineOutlinedIcon fontSize={iconSize} />;
    default: return <DashboardOutlinedIcon fontSize={iconSize} />; // Default icon
  }
};

interface SidebarProps {
  sidebarOpen: boolean;
  drawerWidth: number;
  onToggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ sidebarOpen, drawerWidth, onToggleSidebar }) => {
  const theme = useTheme();
  const location = useLocation();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // Added useMediaQuery import
  const { menuItems: backendMenuItems, isLoadingAuth } = useAuth(); // Also get isLoadingAuth

   console.log("Sidebar: menuItems from AuthContext:", backendMenuItems.length, "items.");
  console.log("Sidebar: isLoadingAuth:", isLoadingAuth);

  const iconSize = sidebarOpen ? 'medium' : 'small';

  // const menuItems = [
  //   { text: 'Dashboard', icon: <DashboardOutlinedIcon fontSize={iconSize} />, path: '/dashboard' },
  //   { text: 'Candidates', icon: <PeopleOutlineOutlinedIcon fontSize={iconSize} />, path: '/candidates' },
  //   { text: 'Job Postings', icon: <WorkOutlineOutlinedIcon fontSize={iconSize} />, path: '/jobs' },
  //   { text: 'Upload Resume', icon: <UploadFileOutlinedIcon fontSize={iconSize} />, path: '/upload-resume' },
  //   { text: 'Analyse Resume', icon: <AnalyticsOutlinedIcon fontSize={sidebarOpen ? 'medium' : 'small'} />, path: '/analyse-resume' }, // <<<<< NEW MENU ITEM
  // ];

  // Process backend menu items to match expected structure
  // Filter out any items the backend might send that you don't want to display
  const processedMenuItems = backendMenuItems.filter(item => 
    item.path && item.displayName // Ensure path and displayName exist
  ).map(item => ({
    text: item.displayName,
    icon: getMuiIconComponent(item.icon, iconSize),
    path: item.path,
    // Add other properties if needed for filtering/ordering
  }));
  //})).sort((a,b) => a.text.localeCompare(b.text)); // Example sorting by text


  const bottomItems = [
    { text: 'Settings', icon: <SettingsOutlinedIcon fontSize={iconSize} />, path: '/settings' },
    { text: 'Help', icon: <HelpOutlineOutlinedIcon fontSize={iconSize} />, path: '/help' },
  ];

  const renderListItem = (item: { text: string, icon: React.ReactElement, path: string }) => {
    const isActive = item.path === '/' && location.pathname === '/' ? true : item.path !== '/' && location.pathname.startsWith(item.path);

    // The ListItemButton is the single child of Tooltip
    const listItemButtonContent = (
      <ListItemButton
        component={NavLink}
        to={item.path}
        selected={isActive}
        onClick={() => {
          if (isMobile) {
            onToggleSidebar();
          }
        }}
        sx={{
          // The theme's MuiListItemButton styleOverrides will handle hover, selected states,
          // border-radius, and margins. We only need to override layout if necessary.
          justifyContent: sidebarOpen ? 'initial' : 'center',
        }}
      >
        <ListItemIcon
          sx={{
            minWidth: 0,
            mr: sidebarOpen ? 1.25 : 'auto', // Reduced space between icon and text (10px)
            justifyContent: 'center',
            // Color is inherited and handled by the theme's MuiListItemButton styles
          }}
        >
          {item.icon}
        </ListItemIcon>
        <ListItemText
          primary={item.text}
          sx={{
            opacity: sidebarOpen ? 1 : 0,
            display: sidebarOpen ? 'block' : 'none',
            whiteSpace: 'nowrap',
            fontWeight: isActive ? 500 : 400,
            transition: theme.transitions.create(['opacity', 'display'], {
              delay: sidebarOpen ? theme.transitions.duration.shortest : 0,
            }),
          }}
        />
      </ListItemButton>
    );

    return (
      <ListItem key={item.text} disablePadding sx={{ display: 'block' }}>
        <Tooltip
          title={!sidebarOpen ? item.text : ""} // Empty title if sidebar is open, effectively disabling tooltip
          placement="right"
          arrow
          PopperProps={{ sx: { visibility: sidebarOpen ? 'hidden' : 'visible' } }}
        >
          {/* Ensuring ListItemButton is the ONLY direct child */}
          {listItemButtonContent}
        </Tooltip>
      </ListItem>
    );
  };

  // const drawerContent = (
  //   <>
  //     <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: sidebarOpen ? 'flex-start' : 'center', px: sidebarOpen ? 2 : 0, py: 2, flexDirection: sidebarOpen ? 'row' : 'column' }}>
  //       <img 
  //         src={sidebarOpen ? "https://placehold.co/32x32/5D87FF/FFFFFF?text=TF" : "https://placehold.co/32x32/5D87FF/FFFFFF?text=T"} 
  //         alt="Logo" 
  //         style={{ height: '32px', marginRight: sidebarOpen ? '12px' : '0px', marginBottom: sidebarOpen ? '0px' : '8px' }} 
  //       />
  //       {sidebarOpen && (
  //         <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 700, whiteSpace: 'nowrap' }}>
  //           TalentFlow
  //         </Typography>
  //       )}
  //     </Toolbar>
  //     <Divider sx={{ borderColor: theme.palette.divider }} />
  //     <Box sx={{ overflowY: 'auto', overflowX: 'hidden', flexGrow: 1, pt: 1 }}>
  //       <List>
  //         {menuItems.map(renderListItem)}
  //       </List>
  //     </Box>
  //     <Divider sx={{ borderColor: theme.palette.divider }} />
  //     <Box sx={{ overflowY: 'auto', overflowX: 'hidden', pb: 1 }}>
  //       <List>
  //         {bottomItems.map(renderListItem)}
  //       </List>
  //     </Box>
  //   </>
  // );

  const drawerContent = (
    <>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', justifyContent: sidebarOpen ? 'flex-start' : 'center', px: sidebarOpen ? 2 : 0, py: 2, flexDirection: sidebarOpen ? 'row' : 'column' }}>
        <img
          src={sidebarOpen ? "https://placehold.co/32x32/5D87FF/FFFFFF?text=TF" : "https://placehold.co/32x32/5D87FF/FFFFFF?text=T"}
          alt="Logo"
          style={{ height: '32px', marginRight: sidebarOpen ? '12px' : '0px', marginBottom: sidebarOpen ? '0px' : '8px' }}
        />
        {sidebarOpen && (
          <Typography variant="h6" sx={{ color: theme.palette.text.primary, fontWeight: 700, whiteSpace: 'nowrap' }}>
            TalentFlow
          </Typography>
        )}
      </Toolbar>
      <Divider sx={{ borderColor: theme.palette.divider }} />
      <Box sx={{ overflowY: 'auto', overflowX: 'hidden', flexGrow: 1 }}>
        <List disablePadding>
          {processedMenuItems.map(renderListItem)} {/* <<<<< USE PROCESSED MENU ITEMS */}
        </List>
      </Box>
      <Divider sx={{ borderColor: theme.palette.divider }}/>
      <Box sx={{ overflowY: 'auto', overflowX: 'hidden' }}>
        <List disablePadding>
          {bottomItems.map(renderListItem)}
        </List>
      </Box>
    </>
  );

  const smCollapsedDrawerWidth = `calc(${theme.spacing(7)} + 1px)`;


  return (
    <Drawer
      variant={isMobile ? "temporary" : "persistent"}
      open={sidebarOpen}
      onClose={isMobile ? onToggleSidebar : undefined}
      ModalProps={{ keepMounted: true }}
      sx={{
        width: sidebarOpen ? drawerWidth : (isMobile ? 0 : smCollapsedDrawerWidth),
        flexShrink: 0,
        whiteSpace: 'nowrap',
        transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: sidebarOpen ? theme.transitions.duration.enteringScreen : theme.transitions.duration.leavingScreen,
        }),
        '& .MuiDrawer-paper': {
          width: 'inherit',
          boxSizing: 'border-box',
          overflowX: 'hidden',
          borderRight: `1px solid ${theme.palette.divider}`,
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: sidebarOpen ? theme.transitions.duration.enteringScreen : theme.transitions.duration.leavingScreen,
          }),
          ...(sidebarOpen && {
            width: drawerWidth,
          }),
          ...(!sidebarOpen && !isMobile && {
            width: smCollapsedDrawerWidth,
          }),
          ...(isMobile && !sidebarOpen && {
            width: 0,
          }),
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

// Ensure useMediaQuery is imported from @mui/material if not already
// import { useMediaQuery } from '@mui/material';
export default Sidebar;