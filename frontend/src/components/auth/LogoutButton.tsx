import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  AccountCircle,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

interface LogoutButtonProps {
  variant?: 'button' | 'menu';
  size?: 'small' | 'medium' | 'large';
}

export function LogoutButton({ variant = 'menu', size = 'medium' }: LogoutButtonProps) {
  const navigate = useNavigate();
  const { user, logout, isLoading } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    handleMenuClose();
    
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleProfile = () => {
    handleMenuClose();
    navigate('/profile');
  };

  const handleSettings = () => {
    handleMenuClose();
    navigate('/settings');
  };

  if (variant === 'button') {
    return (
      <Button
        variant="outlined"
        startIcon={isLoggingOut ? <CircularProgress size={16} /> : <LogoutIcon />}
        onClick={handleLogout}
        disabled={isLoading || isLoggingOut}
        size={size}
      >
        {isLoggingOut ? 'Signing Out...' : 'Sign Out'}
      </Button>
    );
  }

  return (
    <>
      <IconButton
        size={size}
        onClick={handleMenuOpen}
        disabled={isLoading}
        sx={{ ml: 1 }}
      >
        <AccountCircle />
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={handleMenuClose}
        PaperProps={{
          elevation: 3,
          sx: {
            minWidth: 200,
            mt: 1.5,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
            },
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {user && (
          <>
            <Box sx={{ px: 2, py: 1.5 }}>
              <Typography variant="subtitle2" noWrap>
                {user.username}
              </Typography>
              <Typography variant="body2" color="text.secondary" noWrap>
                {user.email}
              </Typography>
              {user.role === 'admin' && (
                <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                  Administrator
                </Typography>
              )}
            </Box>
            <Divider />
          </>
        )}
        
        <MenuItem onClick={handleProfile}>
          <ListItemIcon>
            <PersonIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={handleSettings}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        
        <Divider />
        
        <MenuItem onClick={handleLogout} disabled={isLoggingOut}>
          <ListItemIcon>
            {isLoggingOut ? (
              <CircularProgress size={20} />
            ) : (
              <LogoutIcon fontSize="small" />
            )}
          </ListItemIcon>
          <ListItemText>
            {isLoggingOut ? 'Signing Out...' : 'Sign Out'}
          </ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}