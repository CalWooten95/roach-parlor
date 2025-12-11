import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
  BottomNavigation,
  BottomNavigationAction,
  Paper,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  SportsFootball as WagersIcon,
  Analytics as AnalyticsIcon,
  AdminPanelSettings as AdminIcon,
  LiveTv as LiveIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';

interface NavigationItem {
  label: string;
  path: string;
  icon: React.ReactElement;
  adminOnly?: boolean;
}

const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    path: '/',
    icon: <DashboardIcon />,
  },
  {
    label: 'Wagers',
    path: '/wagers',
    icon: <WagersIcon />,
  },
  {
    label: 'Live Tracking',
    path: '/live',
    icon: <LiveIcon />,
  },
  {
    label: 'Analytics',
    path: '/analytics',
    icon: <AnalyticsIcon />,
  },
  {
    label: 'Admin',
    path: '/admin',
    icon: <AdminIcon />,
    adminOnly: true,
  },
];

export function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Filter navigation items based on user role
  const visibleItems = navigationItems.filter(item => {
    if (item.adminOnly && user?.role !== 'admin') {
      return false;
    }
    return true;
  });

  const currentPath = location.pathname;
  const currentIndex = visibleItems.findIndex(item => {
    if (item.path === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(item.path);
  });

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  if (isMobile) {
    return (
      <Paper
        sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1000 }}
        elevation={3}
      >
        <BottomNavigation
          value={currentIndex >= 0 ? currentIndex : 0}
          onChange={(_, newValue) => {
            const item = visibleItems[newValue];
            if (item) {
              handleNavigation(item.path);
            }
          }}
          showLabels
        >
          {visibleItems.map((item, index) => (
            <BottomNavigationAction
              key={item.path}
              label={item.label}
              icon={item.icon}
            />
          ))}
        </BottomNavigation>
      </Paper>
    );
  }

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Tabs
        value={currentIndex >= 0 ? currentIndex : 0}
        onChange={(_, newValue) => {
          const item = visibleItems[newValue];
          if (item) {
            handleNavigation(item.path);
          }
        }}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ px: 2 }}
      >
        {visibleItems.map((item, index) => (
          <Tab
            key={item.path}
            label={item.label}
            icon={item.icon}
            iconPosition="start"
            sx={{
              minHeight: 48,
              textTransform: 'none',
              fontWeight: currentIndex === index ? 'bold' : 'normal',
            }}
          />
        ))}
      </Tabs>
    </Box>
  );
}