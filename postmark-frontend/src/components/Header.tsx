import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Box,
  Chip,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import {
  Mail as MailIcon,
  Description as DocumentsIcon,
  People as PeopleIcon,
  Person as PersonIcon,
  Upload as UploadIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

// Remove unused User interface - we're using the auth context user type

const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleUpload = () => {
    // TODO: Implement upload modal
    console.log('Upload clicked');
  };

  const getRoleDisplayName = (role: string) => {
    const roleMap: { [key: string]: string } = {
      ADMIN: 'Admin',
      EDITOR: 'Editor',
      VIEWER: 'Viewer',
    };
    return roleMap[role] || 'Viewer';
  };

  const getUserInitials = (user: any) => {
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user?.email) {
      const parts = user.email.split('@')[0].split('.');
      if (parts.length > 1) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return parts[0][0].toUpperCase();
    }
    return 'U';
  };

  const navigationItems = [
    { path: '/documents', label: 'Documents', icon: <DocumentsIcon /> },
    { path: '/users', label: 'Users', icon: <PeopleIcon /> },
    { path: '/references', label: 'References', icon: <PersonIcon /> },
  ];

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar sx={{ justifyContent: 'space-between', px: 3, minHeight: 48 }}>
        {/* Logo and Navigation */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <MailIcon sx={{ color: 'primary.main', fontSize: 24 }} />
            <Typography variant="h6" component="div" sx={{ fontWeight: 500, color: 'primary.main', fontSize: 20 }}>
              Postmark
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {navigationItems.map((item) => (
              <Button
                key={item.path}
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                sx={{
                  color: location.pathname === item.path ? 'primary.main' : 'text.primary',
                  backgroundColor: location.pathname === item.path ? 'primary.light' : 'transparent',
                  borderRadius: '20px',
                  px: 2,
                  py: 1,
                  minHeight: 48,
                  fontSize: 14,
                  fontWeight: 500,
                  '&:hover': {
                    backgroundColor: location.pathname === item.path ? 'primary.light' : 'action.hover',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        </Box>

        {/* Actions and Profile */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={handleUpload}
            sx={{
              backgroundColor: 'primary.main',
              borderRadius: '20px',
              px: 3,
              py: 1,
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
            }}
          >
            Upload
          </Button>

          <IconButton
            onClick={handleProfileMenuOpen}
            sx={{
              width: 40,
              height: 40,
              backgroundColor: 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'primary.dark',
                transform: 'scale(1.05)',
              },
            }}
          >
            <Avatar sx={{ width: 32, height: 32, backgroundColor: 'transparent' }}>
              {user ? getUserInitials(user) : 'U'}
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            sx={{
              '& .MuiPaper-root': {
                borderRadius: '12px',
                minWidth: 280,
                mt: 1,
              },
            }}
          >
            {user && (
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ backgroundColor: 'primary.main', width: 48, height: 48 }}>
                    {getUserInitials(user)}
                  </Avatar>
                  <Box>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {user.first_name} {user.last_name}
                    </Typography>
                    <Chip
                      label={getRoleDisplayName(user.role)}
                      size="small"
                      sx={{ mt: 0.5, fontSize: '12px' }}
                    />
                  </Box>
                </Box>
              </Box>
            )}
            <MenuItem onClick={handleLogout} sx={{ gap: 1 }}>
              <LogoutIcon fontSize="small" />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
