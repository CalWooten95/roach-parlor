import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  BoxProps,
} from '@mui/material';

export interface LoadingSpinnerProps extends BoxProps {
  size?: number | 'small' | 'medium' | 'large';
  message?: string;
  fullScreen?: boolean;
  color?: 'primary' | 'secondary' | 'inherit';
}

export function LoadingSpinner({
  size = 'medium',
  message,
  fullScreen = false,
  color = 'primary',
  ...props
}: LoadingSpinnerProps) {
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 56,
  };

  const spinnerSize = typeof size === 'string' ? sizeMap[size] : size;

  const content = (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      gap={2}
      {...props}
    >
      <CircularProgress
        size={spinnerSize}
        color={color}
        aria-label={message || 'Loading'}
      />
      {message && (
        <Typography
          variant="body2"
          color="text.secondary"
          textAlign="center"
          role="status"
          aria-live="polite"
        >
          {message}
        </Typography>
      )}
    </Box>
  );

  if (fullScreen) {
    return (
      <Box
        position="fixed"
        top={0}
        left={0}
        right={0}
        bottom={0}
        display="flex"
        alignItems="center"
        justifyContent="center"
        bgcolor="rgba(255, 255, 255, 0.8)"
        zIndex={9999}
      >
        {content}
      </Box>
    );
  }

  return content;
}