import React from 'react';
import {
  Card as MuiCard,
  CardContent,
  CardHeader,
  CardActions,
  CardProps as MuiCardProps,
  Typography,
  Box,
  Divider,
} from '@mui/material';

export interface CardProps extends MuiCardProps {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  loading?: boolean;
  padding?: 'none' | 'small' | 'medium' | 'large';
}

export function Card({
  title,
  subtitle,
  actions,
  children,
  loading = false,
  padding = 'medium',
  ...props
}: CardProps) {
  const paddingMap = {
    none: 0,
    small: 1,
    medium: 2,
    large: 3,
  };

  return (
    <MuiCard
      {...props}
      sx={{
        position: 'relative',
        ...props.sx,
      }}
    >
      {(title || subtitle) && (
        <>
          <CardHeader
            title={
              title && (
                <Typography variant="h6" component="h2">
                  {title}
                </Typography>
              )
            }
            subheader={subtitle}
            sx={{ pb: title || subtitle ? 1 : 0 }}
          />
          {children && <Divider />}
        </>
      )}

      <CardContent
        sx={{
          padding: paddingMap[padding],
          '&:last-child': {
            paddingBottom: paddingMap[padding],
          },
        }}
      >
        {loading ? (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: 100,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              Loading...
            </Typography>
          </Box>
        ) : (
          children
        )}
      </CardContent>

      {actions && (
        <>
          <Divider />
          <CardActions sx={{ justifyContent: 'flex-end', p: 2 }}>
            {actions}
          </CardActions>
        </>
      )}
    </MuiCard>
  );
}