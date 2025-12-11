import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Stack,
  TextField,
  FormControlLabel,
  Switch,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  Close as CloseIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { Button } from '@/components/ui/Button';
import { WagerStatus } from '@/types';
import { WagerFilters as WagerFiltersType } from '@/services/wagers';
import { WAGER_STATUSES } from '@/utils/constants';

export interface WagerFiltersProps {
  filters: WagerFiltersType;
  onFiltersChange: (filters: WagerFiltersType) => void;
  onClose: () => void;
}

export function WagerFilters({ filters, onFiltersChange, onClose }: WagerFiltersProps) {
  const [localFilters, setLocalFilters] = useState<WagerFiltersType>(filters);

  const handleStatusChange = (status: WagerStatus) => {
    const currentStatuses = localFilters.status || [];
    const newStatuses = currentStatuses.includes(status)
      ? currentStatuses.filter(s => s !== status)
      : [...currentStatuses, status];
    
    setLocalFilters({
      ...localFilters,
      status: newStatuses.length > 0 ? newStatuses : undefined,
    });
  };

  const handleDateChange = (field: 'dateFrom' | 'dateTo', value: string) => {
    setLocalFilters({
      ...localFilters,
      [field]: value || undefined,
    });
  };

  const handleSortChange = (field: 'sortBy' | 'sortOrder', value: string) => {
    setLocalFilters({
      ...localFilters,
      [field]: value || undefined,
    });
  };

  const handleArchivedChange = (archived: boolean | undefined) => {
    setLocalFilters({
      ...localFilters,
      archived,
    });
  };

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    onClose();
  };

  const handleClearFilters = () => {
    const clearedFilters: WagerFiltersType = {};
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const hasActiveFilters = Boolean(
    localFilters.status?.length ||
    localFilters.archived !== undefined ||
    localFilters.dateFrom ||
    localFilters.dateTo ||
    localFilters.sortBy
  );

  return (
    <Collapse in={true}>
      <Paper sx={{ p: 3, mb: 2, border: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">Filters</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>

        <Stack spacing={3}>
          {/* Status Filter */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Status
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {Object.values(WAGER_STATUSES).map((status) => (
                <Chip
                  key={status}
                  label={status.charAt(0).toUpperCase() + status.slice(1)}
                  variant={localFilters.status?.includes(status as WagerStatus) ? 'filled' : 'outlined'}
                  onClick={() => handleStatusChange(status as WagerStatus)}
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Box>

          {/* Archive Filter */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Archive Status
            </Typography>
            <Stack direction="row" spacing={1}>
              <Chip
                label="All"
                variant={localFilters.archived === undefined ? 'filled' : 'outlined'}
                onClick={() => handleArchivedChange(undefined)}
              />
              <Chip
                label="Active"
                variant={localFilters.archived === false ? 'filled' : 'outlined'}
                onClick={() => handleArchivedChange(false)}
              />
              <Chip
                label="Archived"
                variant={localFilters.archived === true ? 'filled' : 'outlined'}
                onClick={() => handleArchivedChange(true)}
              />
            </Stack>
          </Box>

          {/* Date Range */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Date Range
            </Typography>
            <Stack direction="row" spacing={2}>
              <TextField
                label="From"
                type="date"
                value={localFilters.dateFrom || ''}
                onChange={(e) => handleDateChange('dateFrom', e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
                sx={{ flex: 1 }}
              />
              <TextField
                label="To"
                type="date"
                value={localFilters.dateTo || ''}
                onChange={(e) => handleDateChange('dateTo', e.target.value)}
                InputLabelProps={{ shrink: true }}
                size="small"
                sx={{ flex: 1 }}
              />
            </Stack>
          </Box>

          {/* Sorting */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Sort By
            </Typography>
            <Stack direction="row" spacing={2}>
              <FormControl size="small" sx={{ flex: 1 }}>
                <InputLabel>Sort Field</InputLabel>
                <Select
                  value={localFilters.sortBy || ''}
                  label="Sort Field"
                  onChange={(e) => handleSortChange('sortBy', e.target.value)}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="createdAt">Created Date</MenuItem>
                  <MenuItem value="amount">Amount</MenuItem>
                  <MenuItem value="status">Status</MenuItem>
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ flex: 1 }}>
                <InputLabel>Order</InputLabel>
                <Select
                  value={localFilters.sortOrder || 'desc'}
                  label="Order"
                  onChange={(e) => handleSortChange('sortOrder', e.target.value)}
                  disabled={!localFilters.sortBy}
                >
                  <MenuItem value="asc">Ascending</MenuItem>
                  <MenuItem value="desc">Descending</MenuItem>
                </Select>
              </FormControl>
            </Stack>
          </Box>

          {/* Actions */}
          <Stack direction="row" spacing={2} justifyContent="flex-end">
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={handleClearFilters}
              disabled={!hasActiveFilters}
            >
              Clear All
            </Button>
            <Button variant="contained" onClick={handleApplyFilters}>
              Apply Filters
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Collapse>
  );
}