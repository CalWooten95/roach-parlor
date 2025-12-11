import React, { useState, useCallback } from 'react';
import { Box, Alert, Snackbar } from '@mui/material';
import { WagerList } from '@/components/wagers';
import { useWagers, useUpdateWagerStatus, useArchiveWager, useDeleteWager } from '@/hooks/useWagers';
import { WagerFilters } from '@/services/wagers';
import { WagerStatus } from '@/types';

export function Wagers() {
  const [filters, setFilters] = useState<WagerFilters>({
    archived: false, // Show only active wagers by default
    sortBy: 'createdAt',
    sortOrder: 'desc',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const pageSize = 12;

  // Fetch wagers with current filters and pagination
  const {
    data: wagersResponse,
    isLoading: isLoadingWagers,
    error,
    refetch,
  } = useWagers({
    ...filters,
    page: currentPage,
    pageSize,
  });

  // Mutations
  const updateStatusMutation = useUpdateWagerStatus();
  const archiveMutation = useArchiveWager();
  const deleteMutation = useDeleteWager();

  // Event handlers
  const handleFiltersChange = useCallback((newFilters: WagerFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleWagerStatusUpdate = useCallback(
    async (wagerId: number, status: WagerStatus) => {
      try {
        await updateStatusMutation.mutateAsync({ id: wagerId, status });
        setSnackbar({
          open: true,
          message: `Wager status updated to ${status}`,
          severity: 'success',
        });
      } catch (error) {
        setSnackbar({
          open: true,
          message: 'Failed to update wager status',
          severity: 'error',
        });
      }
    },
    [updateStatusMutation]
  );

  const handleWagerArchive = useCallback(
    async (wagerId: number, archived: boolean) => {
      try {
        await archiveMutation.mutateAsync({ id: wagerId, archived });
        setSnackbar({
          open: true,
          message: archived ? 'Wager archived' : 'Wager unarchived',
          severity: 'success',
        });
      } catch (error) {
        setSnackbar({
          open: true,
          message: `Failed to ${archived ? 'archive' : 'unarchive'} wager`,
          severity: 'error',
        });
      }
    },
    [archiveMutation]
  );

  const handleWagerDelete = useCallback(
    async (wagerId: number) => {
      try {
        await deleteMutation.mutateAsync(wagerId);
        setSnackbar({
          open: true,
          message: 'Wager deleted',
          severity: 'success',
        });
      } catch (error) {
        setSnackbar({
          open: true,
          message: 'Failed to delete wager',
          severity: 'error',
        });
      }
    },
    [deleteMutation]
  );

  const handleCreateWager = useCallback(() => {
    // TODO: Implement wager creation modal/form in a future task
    setSnackbar({
      open: true,
      message: 'Wager creation will be implemented in a future task',
      severity: 'info',
    });
  }, []);

  const handleWagerEdit = useCallback(() => {
    // TODO: Implement wager editing modal/form in a future task
    setSnackbar({
      open: true,
      message: 'Wager editing will be implemented in a future task',
      severity: 'info',
    });
  }, []);

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const isLoading = 
    isLoadingWagers || 
    updateStatusMutation.isPending || 
    archiveMutation.isPending || 
    deleteMutation.isPending;

  return (
    <Box sx={{ p: 3 }}>
      <WagerList
        wagers={wagersResponse?.data || []}
        loading={isLoading}
        error={error?.message}
        totalCount={wagersResponse?.total || 0}
        currentPage={currentPage}
        pageSize={pageSize}
        filters={filters}
        onRefresh={refetch}
        onPageChange={handlePageChange}
        onFiltersChange={handleFiltersChange}
        onWagerStatusUpdate={handleWagerStatusUpdate}
        onWagerArchive={handleWagerArchive}
        onWagerDelete={handleWagerDelete}
        onWagerEdit={handleWagerEdit}
        onCreateWager={handleCreateWager}
        showBulkActions={true}
      />

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}