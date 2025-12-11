import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { LogoutButton } from '../auth/LogoutButton';
import { Navigation } from './Navigation';

interface AppLayoutProps {
  children?: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Don't show layout on login page
  if (location.pathname === '/login') {
    return <>{children || <Outlet />}</>;
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 'bold',
              cursor: 'pointer',
            }}
          >
            🪳 Roach Parlor
          </Typography>

          {isAuthenticated && user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {!isMobile && (
                <Typography variant="body2" sx={{ mr: 1 }}>
                  Welcome, {user.username}
                </Typography>
              )}
              <LogoutButton />
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {isAuthenticated && <Navigation />}

      <Box component="main" sx={{ flexGrow: 1, py: 3 }}>
        <Container maxWidth="lg">
          {children || <Outlet />}
        </Container>
      </Box>
    </Box>
  );
}