import React from 'react';
import {
  Button as MuiButton,
  ButtonProps as MuiButtonProps,
  CircularProgress,
  Box,
} from '@mui/material';

export interface ButtonProps extends Omit<MuiButtonProps, 'size'> {
  loading?: boolean;
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
  'aria-label'?: string;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ loading = false, children, disabled, size = 'medium', ...props }, ref) => {
    return (
      <MuiButton
        ref={ref}
        disabled={disabled || loading}
        size={size}
        {...props}
        sx={{
          position: 'relative',
          ...props.sx,
        }}
      >
        {loading && (
          <Box
            sx={{
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress
              size={size === 'small' ? 16 : size === 'large' ? 24 : 20}
              color="inherit"
            />
          </Box>
        )}
        <Box
          sx={{
            visibility: loading ? 'hidden' : 'visible',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          {children}
        </Box>
      </MuiButton>
    );
  }
);

Button.displayName = 'Button';