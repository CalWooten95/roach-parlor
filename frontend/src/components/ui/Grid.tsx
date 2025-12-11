import React from 'react';
import {
  Grid as MuiGrid,
  GridProps as MuiGridProps,
  Box,
  useTheme,
  useMediaQuery,
} from '@mui/material';

export interface GridProps extends MuiGridProps {
  children: React.ReactNode;
  spacing?: number;
  responsive?: boolean;
}

export function Grid({ children, spacing = 2, responsive = true, ...props }: GridProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Adjust spacing for mobile devices
  const adjustedSpacing = responsive && isMobile ? Math.max(1, spacing - 1) : spacing;

  return (
    <MuiGrid container spacing={adjustedSpacing} {...props}>
      {children}
    </MuiGrid>
  );
}

export interface GridItemProps extends MuiGridProps {
  children: React.ReactNode;
  xs?: number | 'auto';
  sm?: number | 'auto';
  md?: number | 'auto';
  lg?: number | 'auto';
  xl?: number | 'auto';
}

export function GridItem({ children, ...props }: GridItemProps) {
  return (
    <MuiGrid item {...props}>
      {children}
    </MuiGrid>
  );
}

// Responsive container with max-width and centering
export interface ResponsiveContainerProps {
  children: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
  padding?: number;
  disableGutters?: boolean;
}

export function ResponsiveContainer({
  children,
  maxWidth = 'lg',
  padding = 2,
  disableGutters = false,
}: ResponsiveContainerProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: maxWidth ? theme.breakpoints.values[maxWidth] : 'none',
        margin: '0 auto',
        padding: disableGutters ? 0 : isMobile ? padding / 2 : padding,
      }}
    >
      {children}
    </Box>
  );
}

// Flexible layout component
export interface FlexBoxProps {
  children: React.ReactNode;
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse';
  justify?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
  align?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  wrap?: 'nowrap' | 'wrap' | 'wrap-reverse';
  gap?: number;
  responsive?: boolean;
  sx?: any;
}

export function FlexBox({
  children,
  direction = 'row',
  justify = 'flex-start',
  align = 'stretch',
  wrap = 'nowrap',
  gap = 0,
  responsive = true,
  sx,
}: FlexBoxProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Switch to column layout on mobile for better UX
  const responsiveDirection = responsive && isMobile && direction === 'row' ? 'column' : direction;

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: responsiveDirection,
        justifyContent: justify,
        alignItems: align,
        flexWrap: wrap,
        gap: gap,
        ...sx,
      }}
    >
      {children}
    </Box>
  );
}