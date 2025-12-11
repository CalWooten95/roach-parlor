import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Stack,
  Grid,
  Alert,
  Skeleton,
  Fab,
  Checkbox,
  FormControlLabel,
  Menu,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { WagerCard } from './WagerCard';
import { WagerFilters } from './WagerFilters';
import { Button } from '@/components/ui/Button';
import { SearchInput } from '@/components/ui/SearchInput';
import { Pagination } from '@/components/ui/Pagination';
import { Wager, WagerStatus } from '@/types';
import { WagerFilters as WagerFiltersType } from '@/services/wagers';

export interface WagerListProps {
  wagers: Wager[];
  loading: boolean;
  error?: string;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  filters: WagerFiltersType;
  onRefresh: () => void;
  onPageChange: (page: number) => void;
  onFiltersChange: (filters: WagerFiltersType) => void;
  onWagerStatusUpdate: (wagerId: number, status: WagerStatus) => void;
  onWagerArchive: (wagerId: number, archived: boolean) => void;
  onWagerDelete: (wagerId: number) => void;
  onWagerEdit?: (wager: Wager) => void;
  onCreateWager?: () => void;
  showBulkActions?: boolean;
}

export function WagerList({
  wagers,
  loading,
  error,
  totalCount,
  currentPage,
  pageSize,
  filters,
  onRefresh,
  onPageChange,
  onFiltersChange,
  onWagerStatusUpdate,
  onWagerArchive,
  onWagerDelete,
  onWagerEdit,
  onCreateWager,
  showBulkActions = false,
}: WagerListProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [selectedWagers, setSelectedWagers] = useState<Set<number>>(new Set());
  const [bulkMenuAnchor, setBulkMenuAnchor] = useState<null | HTMLElement>(null);

  const totalPages = Math.ceil(totalCount / pageSize);

  // Handle search
  const handleSearchChange = (search: string) => {
    onFiltersChange({ ...filters, search });
  };

  // Handle bulk selection
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedWagers(new Set(wagers.map((w: Wager) => w.id)));
    } else {
      setSelectedWagers(new Set());
    }
  };

  const handleSelectWager = (wagerId: number, checked: boolean) => {
    const newSelected = new Set(selectedWagers);
    if (checked) {
      newSelected.add(wagerId);
    } else {
      newSelected.delete(wagerId);
    }
    setSelectedWagers(newSelected);
  };

  // Bulk actions
  const handleBulkMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setBulkMenuAnchor(event.currentTarget);
  };

  const handleBulkMenuClose = () => {
    setBulkMenuAnchor(null);
  };

  const handleBulkStatusUpdate = (status: WagerStatus) => {
    selectedWagers.forEach((wagerId: number) => {
      onWagerStatusUpdate(wagerId, status);
    });
    setSelectedWagers(new Set());
    handleBulkMenuClose();
  };

  const handleBulkArchive = (archived: boolean) => {
    selectedWagers.forEach((wagerId: number) => {
      onWagerArchive(wagerId, archived);
    });
    setSelectedWagers(new Set());
    handleBulkMenuClose();
  };

  const handleBulkDelete = () => {
    selectedWagers.forEach((wagerId: number) => {
      onWagerDelete(wagerId);
    });
    setSelectedWagers(new Set());
    handleBulkMenuClose();
  };

  // Memoized values
  const allSelected = useMemo(() => {
    return wagers.length > 0 && selectedWagers.size === wagers.length;
  }, [wagers.length, selectedWagers.size]);

  const someSelected = useMemo(() => {
    return selectedWagers.size > 0 && selectedWagers.size < wagers.length;
  }, [selectedWagers.size, wagers.length]);

  const hasSelection = selectedWagers.size > 0;

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        <Typography variant="body2">
          {error}
        </Typography>
        <Button onClick={onRefresh} sx={{ mt: 1 }}>
          Try Again
        </Button>
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4" component="h1">
            Wagers
          </Typography>
          {onCreateWager && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={onCreateWager}
            >
              New Wager
            </Button>
          )}
        </Box>

        {/* Search and Filter Controls */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <SearchInput
            placeholder="Search wagers..."
            value={filters.search || ''}
            onChange={handleSearchChange}
            sx={{ flex: 1 }}
          />
          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button variant="outlined" onClick={onRefresh} disabled={loading}>
            Refresh
          </Button>
        </Stack>

        {/* Bulk Actions */}
        {showBulkActions && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={allSelected}
                  indeterminate={someSelected}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleSelectAll(e.target.checked)}
                />
              }
              label="Select All"
            />
            {hasSelection && (
              <>
                <Typography variant="body2" color="text.secondary">
                  {selectedWagers.size} selected
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<MoreVertIcon />}
                  onClick={handleBulkMenuOpen}
                >
                  Bulk Actions
                </Button>
              </>
            )}
          </Box>
        )}

        {/* Filters Panel */}
        {showFilters && (
          <WagerFilters
            filters={filters}
            onFiltersChange={onFiltersChange}
            onClose={() => setShowFilters(false)}
          />
        )}
      </Box>

      {/* Loading State */}
      {loading && (
        <Grid container spacing={2}>
          {Array.from({ length: pageSize }).map((_, index) => (
            <Grid item xs={12} md={6} lg={4} key={index}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty State */}
      {!loading && wagers.length === 0 && (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            py: 8,
            textAlign: 'center',
          }}
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No wagers found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {filters.search || filters.status?.length || filters.archived !== undefined
              ? 'Try adjusting your filters or search terms.'
              : 'Get started by creating your first wager.'}
          </Typography>
          {onCreateWager && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={onCreateWager}>
              Create Wager
            </Button>
          )}
        </Box>
      )}

      {/* Wager Grid */}
      {!loading && wagers.length > 0 && (
        <>
          <Grid container spacing={2}>
            {wagers.map((wager) => (
              <Grid item xs={12} md={6} lg={4} key={wager.id}>
                {showBulkActions && (
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <Checkbox
                      checked={selectedWagers.has(wager.id)}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleSelectWager(wager.id, e.target.checked)}
                      sx={{ mt: 1 }}
                    />
                    <Box sx={{ flex: 1 }}>
                      <WagerCard
                        wager={wager}
                        onStatusUpdate={onWagerStatusUpdate}
                        onArchive={onWagerArchive}
                        onDelete={onWagerDelete}
                        onEdit={onWagerEdit || undefined}
                        showActions={!hasSelection}
                      />
                    </Box>
                  </Box>
                )}
                {!showBulkActions && (
                  <WagerCard
                    wager={wager}
                    onStatusUpdate={onWagerStatusUpdate}
                    onArchive={onWagerArchive}
                    onDelete={onWagerDelete}
                    onEdit={onWagerEdit || undefined}
                  />
                )}
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                pageSize={pageSize}
                totalItems={totalCount}
                onPageChange={onPageChange}
              />
            </Box>
          )}
        </>
      )}

      {/* Floating Action Button */}
      {onCreateWager && !loading && (
        <Fab
          color="primary"
          aria-label="Create wager"
          onClick={onCreateWager}
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
          }}
        >
          <AddIcon />
        </Fab>
      )}

      {/* Bulk Actions Menu */}
      <Menu
        anchorEl={bulkMenuAnchor}
        open={Boolean(bulkMenuAnchor)}
        onClose={handleBulkMenuClose}
      >
        <MenuItem onClick={() => handleBulkStatusUpdate('won')}>
          Mark as Won
        </MenuItem>
        <MenuItem onClick={() => handleBulkStatusUpdate('lost')}>
          Mark as Lost
        </MenuItem>
        <MenuItem onClick={() => handleBulkStatusUpdate('push')}>
          Mark as Push
        </MenuItem>
        <MenuItem onClick={() => handleBulkStatusUpdate('cancelled')}>
          Mark as Cancelled
        </MenuItem>
        <Divider />
        <MenuItem onClick={() => handleBulkArchive(true)}>
          Archive Selected
        </MenuItem>
        <MenuItem onClick={() => handleBulkArchive(false)}>
          Unarchive Selected
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleBulkDelete} sx={{ color: 'error.main' }}>
          Delete Selected
        </MenuItem>
      </Menu>
    </Box>
  );
}