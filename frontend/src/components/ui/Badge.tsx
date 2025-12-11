import React from 'react';
import {
  Chip,
  ChipProps,
  Badge as MuiBadge,
  BadgeProps as MuiBadgeProps,
} from '@mui/material';

// Status Badge Component
export interface StatusBadgeProps extends Omit<ChipProps, 'color'> {
  status: 'won' | 'lost' | 'pending' | 'push' | 'cancelled' | 'archived' | 'live';
  size?: 'small' | 'medium';
}

export function StatusBadge({ status, size = 'small', ...props }: StatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'won':
        return { color: 'success' as const, label: 'Won' };
      case 'lost':
        return { color: 'error' as const, label: 'Lost' };
      case 'pending':
        return { color: 'warning' as const, label: 'Pending' };
      case 'push':
        return { color: 'info' as const, label: 'Push' };
      case 'cancelled':
        return { color: 'default' as const, label: 'Cancelled' };
      case 'archived':
        return { color: 'default' as const, label: 'Archived' };
      case 'live':
        return { color: 'info' as const, label: 'Live' };
      default:
        return { color: 'default' as const, label: status };
    }
  };

  const config = getStatusConfig(status);

  return (
    <Chip
      {...props}
      label={config.label}
      color={config.color}
      size={size}
      variant="filled"
      sx={{
        fontWeight: 500,
        textTransform: 'uppercase',
        fontSize: size === 'small' ? '0.75rem' : '0.875rem',
        ...props.sx,
      }}
    />
  );
}

// Notification Badge Component
export interface NotificationBadgeProps extends MuiBadgeProps {
  children: React.ReactNode;
  count?: number;
  showZero?: boolean;
  max?: number;
}

export function NotificationBadge({
  children,
  count = 0,
  showZero = false,
  max = 99,
  ...props
}: NotificationBadgeProps) {
  return (
    <MuiBadge
      {...props}
      badgeContent={count}
      showZero={showZero}
      max={max}
      color="error"
      sx={{
        '& .MuiBadge-badge': {
          fontSize: '0.75rem',
          height: 20,
          minWidth: 20,
        },
        ...props.sx,
      }}
    >
      {children}
    </MuiBadge>
  );
}