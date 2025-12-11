import React from 'react';
import {
  Box,
  Container,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  useTheme,
  useMediaQuery,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';

// Page Layout Component
export interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  breadcrumbs?: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  padding?: boolean;
  fullHeight?: boolean;
}

export function PageLayout({
  children,
  title,
  subtitle,
  actions,
  breadcrumbs,
  maxWidth = 'lg',
  padding = true,
  fullHeight = false,
}: PageLayoutProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box
      sx={{
        minHeight: fullHeight ? '100vh' : 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Page Header */}
      {(title || subtitle || actions || breadcrumbs) && (
        <Box
          sx={{
            borderBottom: `1px solid ${theme.palette.divider}`,
            backgroundColor: 'background.paper',
            py: 2,
          }}
        >
          <Container maxWidth={maxWidth}>
            {breadcrumbs && (
              <Box sx={{ mb: 1 }}>
                {breadcrumbs}
              </Box>
            )}
            
            <Box
              sx={{
                display: 'flex',
                flexDirection: isMobile ? 'column' : 'row',
                justifyContent: 'space-between',
                alignItems: isMobile ? 'flex-start' : 'center',
                gap: 2,
              }}
            >
              <Box>
                {title && (
                  <Typography
                    variant="h4"
                    component="h1"
                    sx={{
                      fontWeight: 600,
                      fontSize: isMobile ? '1.5rem' : '2rem',
                    }}
                  >
                    {title}
                  </Typography>
                )}
                {subtitle && (
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{ mt: 0.5 }}
                  >
                    {subtitle}
                  </Typography>
                )}
              </Box>
              
              {actions && (
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {actions}
                </Box>
              )}
            </Box>
          </Container>
        </Box>
      )}

      {/* Page Content */}
      <Box sx={{ flexGrow: 1 }}>
        <Container
          maxWidth={maxWidth}
          sx={{
            py: padding ? (isMobile ? 2 : 3) : 0,
            px: padding ? undefined : 0,
          }}
        >
          {children}
        </Container>
      </Box>
    </Box>
  );
}

// Sidebar Layout Component
export interface SidebarItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  href?: string;
  onClick?: () => void;
  children?: SidebarItem[];
  badge?: React.ReactNode;
  disabled?: boolean;
}

export interface SidebarLayoutProps {
  children: React.ReactNode;
  sidebarItems: SidebarItem[];
  sidebarWidth?: number;
  sidebarHeader?: React.ReactNode;
  sidebarFooter?: React.ReactNode;
  onItemClick?: (item: SidebarItem) => void;
  activeItemId?: string;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export function SidebarLayout({
  children,
  sidebarItems,
  sidebarWidth = 280,
  sidebarHeader,
  sidebarFooter,
  onItemClick,
  activeItemId,
  collapsible = true,
  defaultCollapsed = false,
}: SidebarLayoutProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);
  const [expandedItems, setExpandedItems] = React.useState<Set<string>>(new Set());

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleItemClick = (item: SidebarItem) => {
    if (item.children) {
      const newExpanded = new Set(expandedItems);
      if (newExpanded.has(item.id)) {
        newExpanded.delete(item.id);
      } else {
        newExpanded.add(item.id);
      }
      setExpandedItems(newExpanded);
    } else {
      if (onItemClick) {
        onItemClick(item);
      }
      if (item.onClick) {
        item.onClick();
      }
      if (isMobile) {
        setMobileOpen(false);
      }
    }
  };

  const renderSidebarItems = (items: SidebarItem[], level = 0) => {
    return items.map((item) => (
      <React.Fragment key={item.id}>
        <ListItem disablePadding sx={{ display: 'block' }}>
          <ListItemButton
            onClick={() => handleItemClick(item)}
            disabled={item.disabled}
            selected={activeItemId === item.id}
            sx={{
              minHeight: 48,
              justifyContent: collapsed ? 'center' : 'initial',
              px: 2.5,
              pl: level > 0 ? 2.5 + (level * 2) : 2.5,
            }}
          >
            {item.icon && (
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: collapsed ? 'auto' : 3,
                  justifyContent: 'center',
                }}
              >
                {item.icon}
              </ListItemIcon>
            )}
            
            {!collapsed && (
              <>
                <ListItemText
                  primary={item.label}
                  sx={{ opacity: collapsed ? 0 : 1 }}
                />
                
                {item.badge && (
                  <Box sx={{ ml: 1 }}>
                    {item.badge}
                  </Box>
                )}
                
                {item.children && (
                  expandedItems.has(item.id) ? <ExpandLess /> : <ExpandMore />
                )}
              </>
            )}
          </ListItemButton>
        </ListItem>
        
        {item.children && !collapsed && (
          <Collapse in={expandedItems.has(item.id)} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {renderSidebarItems(item.children, level + 1)}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    ));
  };

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {sidebarHeader && (
        <>
          <Box sx={{ p: 2 }}>
            {sidebarHeader}
          </Box>
          <Divider />
        </>
      )}
      
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {renderSidebarItems(sidebarItems)}
        </List>
      </Box>
      
      {sidebarFooter && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            {sidebarFooter}
          </Box>
        </>
      )}
    </Box>
  );

  const drawerWidth = collapsed ? 64 : sidebarWidth;

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* Mobile App Bar */}
      {isMobile && (
        <AppBar
          position="fixed"
          sx={{
            width: '100%',
            zIndex: theme.zIndex.drawer + 1,
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div">
              Menu
            </Typography>
          </Toolbar>
        </AppBar>
      )}

      {/* Sidebar */}
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: sidebarWidth,
            },
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
            <IconButton onClick={handleDrawerToggle}>
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          {drawer}
        </Drawer>
        
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              transition: theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
            },
          }}
          open
        >
          {collapsible && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
              <IconButton onClick={() => setCollapsed(!collapsed)}>
                <MenuIcon />
              </IconButton>
            </Box>
          )}
          {drawer}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: { xs: 7, md: 0 }, // Account for mobile app bar
          overflow: 'auto',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}