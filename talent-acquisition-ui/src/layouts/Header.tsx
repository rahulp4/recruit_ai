// src/layouts/Header.tsx
import React from 'react';
import {
  AppBar, Toolbar, IconButton, Typography, Box, Avatar, Menu, MenuItem, Tooltip, InputBase,
  alpha, styled, Badge, ListItemIcon, useTheme, useMediaQuery, Divider
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined';
import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined';
import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import { useAuth } from '../hooks/useAuth'; // Your hook to get user info
import { auth as firebaseAuth } from '../App'; // Firebase auth instance
import { signOut } from 'firebase/auth';
import { useNavigate, Link as RouterLink } from 'react-router-dom';

// Styled components for Search bar (ensure these are defined in your file)
const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.default,
  '&:hover': {
    backgroundColor: theme.palette.divider,
  },
  marginRight: theme.spacing(2),
  marginLeft: 0,
  width: '100%',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto',
  },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: theme.palette.text.secondary,
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: theme.palette.text.primary,
  width: '100%',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1.25, 1.25, 1.25, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '25ch',
      '&:focus': {
        width: '35ch',
      },
    },
  },
}));


interface HeaderProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  drawerWidth: number;
  collapsedDrawerWidth: string;
}

const Header: React.FC<HeaderProps> = ({ sidebarOpen, onToggleSidebar, drawerWidth, collapsedDrawerWidth }) => {
  const { firebaseUser, appUser, logout, role, features } = useAuth(); // <<<<< Use firebaseUser and appUser
  const navigate = useNavigate();
  const theme = useTheme();
  const isSmUp = useMediaQuery(theme.breakpoints.up('sm'));

  const [anchorElUser, setAnchorElUser] = React.useState<null | HTMLElement>(null);
  const [anchorElNotifications, setAnchorElNotifications] = React.useState<null | HTMLElement>(null);

  const handleOpenUserMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorElUser(event.currentTarget);
  const handleCloseUserMenu = () => setAnchorElUser(null);
  const handleOpenNotificationsMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorElNotifications(event.currentTarget);
  const handleCloseNotificationsMenu = () => setAnchorElNotifications(null);

  const handleLogout = async () => {
    handleCloseUserMenu();
    await logout();
    navigate('/login');
  };

  const currentAppBarShift = isSmUp ? (sidebarOpen ? `${drawerWidth}px` : collapsedDrawerWidth) : '0px';
  const currentAppBarWidth = isSmUp ? `calc(100% - ${currentAppBarShift})` : '100%';

  // Prioritize backend-provided email/name, then Firebase
  const userDisplayName = appUser?.email || firebaseUser?.displayName || firebaseUser?.email || 'User';

  // Determine Avatar content
  let avatarContent: string | undefined = undefined;
  if (appUser) { // Use appUser for display
    if (appUser.email) {
      avatarContent = appUser.email[0].toUpperCase();
    } else if (appUser.roles && appUser.roles.length > 0) { // Fallback to role if no email
        avatarContent = appUser.roles[0][0].toUpperCase();
    } else {
      avatarContent = 'U';
    }
  } else if (firebaseUser) { // Fallback to firebaseUser if appUser not loaded yet
    if (firebaseUser.displayName) {
      avatarContent = firebaseUser.displayName[0].toUpperCase();
    } else if (firebaseUser.email) {
      avatarContent = firebaseUser.email[0].toUpperCase();
    } else {
      avatarContent = 'U';
    }
  } else {
    avatarContent = 'U';
  }


  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: theme.zIndex.drawer + 1,
        width: currentAppBarWidth,
        marginLeft: currentAppBarShift,
        transition: theme.transitions.create(['width', 'margin'], {
          easing: theme.transitions.easing.sharp,
          duration: sidebarOpen ? theme.transitions.duration.enteringScreen : theme.transitions.duration.leavingScreen,
        }),
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', paddingLeft: { xs: 1, sm: 2 }, paddingRight: { xs: 1, sm: 2 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton
            color="inherit"
            aria-label="toggle drawer"
            onClick={onToggleSidebar}
            edge="start"
            sx={{ mr: { xs: 0.5, sm: 2 } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6" noWrap component={RouterLink} to="/dashboard"
            sx={{ display: { xs: 'none', sm: 'block' }, fontWeight: 700, color: 'inherit', textDecoration: 'none' }}
          >
            TalentFlow AI
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: {xs: 0.5, sm: 1} }}>
          <Search sx={{ display: { xs: 'none', md: 'flex' } }}>
            <SearchIconWrapper><SearchIcon /></SearchIconWrapper>
            <StyledInputBase placeholder="Search…" inputProps={{ 'aria-label': 'search' }} />
          </Search>

          <Tooltip title="Notifications">
            <IconButton color="inherit" onClick={handleOpenNotificationsMenu}>
              <Badge badgeContent={3} color="error">
                <NotificationsNoneOutlinedIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          <Menu
            id="menu-notifications"
            anchorEl={anchorElNotifications}
            open={Boolean(anchorElNotifications)}
            onClose={handleCloseNotificationsMenu}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            slotProps={{
              paper: {
                sx: {
                  mt: 1.5,
                  minWidth: 280,
                },
              },
            }}
          >
            <MenuItem sx={{fontWeight: 'bold'}}><Typography variant="subtitle1">Notifications</Typography></MenuItem>
            <Divider />
            <MenuItem onClick={handleCloseNotificationsMenu}><Typography variant="body2">Notification 1: New Candidate Applied</Typography></MenuItem>
            <MenuItem onClick={handleCloseNotificationsMenu}><Typography variant="body2">Notification 2: Interview Reminder</Typography></MenuItem>
            <MenuItem onClick={handleCloseNotificationsMenu}><Typography variant="body2">Notification 3: System Update</Typography></MenuItem>
            <Divider />
            <MenuItem sx={{justifyContent: 'center'}} onClick={handleCloseNotificationsMenu}><Typography variant="caption">View All Notifications</Typography></MenuItem>
          </Menu>

          <Tooltip title="Account">
            <IconButton onClick={handleOpenUserMenu} sx={{ p: 0, ml: {xs: 0.5, sm:1} }}>
              <Avatar 
                alt={userDisplayName}
                src={firebaseUser?.photoURL || undefined } 
                sx={{ width: 36, height: 36 }} 
              >
                {avatarContent}
              </Avatar>
            </IconButton>
          </Tooltip>
          <Menu
            id="menu-appbar-user"
            anchorEl={anchorElUser}
            open={Boolean(anchorElUser)}
            onClose={handleCloseUserMenu}
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            transformOrigin={{ vertical: 'top', horizontal: 'right' }}
            slotProps={{
              paper: {
                sx: {
                  mt: 1.5,
                  minWidth: 220,
                  '& .MuiAvatar-root': {
                    width: 32,
                    height: 32,
                    ml: -0.5,
                    mr: 1,
                  },
                },
              },
            }}
          >
            <Box sx={{ px: 2, py: 1.5 }}>
              <Typography variant="subtitle1" fontWeight="bold">{userDisplayName}</Typography>
              <Typography variant="caption" color="text.secondary">{appUser?.email}</Typography> {/* <<<<< Use appUser.email */}
              {role && <Typography variant="caption" color="text.secondary" sx={{mt:0.5}} display="block">Role: {role}</Typography>}
            </Box>
            <Divider />
            <MenuItem onClick={() => { navigate('/profile'); handleCloseUserMenu(); }}>
              <ListItemIcon sx={{minWidth: 36}}><AccountCircleOutlinedIcon fontSize="small" /></ListItemIcon>My Profile
            </MenuItem>
            <MenuItem onClick={handleLogout}>
               <ListItemIcon sx={{minWidth: 36}}><LogoutOutlinedIcon fontSize="small" /></ListItemIcon>Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;