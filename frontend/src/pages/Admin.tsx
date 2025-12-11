import React from 'react';
import { Box, Typography } from '@mui/material';

export function Admin() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Admin Panel
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Admin functionality will be implemented in later tasks.
      </Typography>
    </Box>
  );
}