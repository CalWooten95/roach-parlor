import React from 'react';
import {
  Box,
  Pagination as MuiPagination,
  PaginationItem,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
  NavigateBefore as PrevIcon,
  NavigateNext as NextIcon,
} from '@mui/icons-material';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  showPageSizeSelector?: boolean;
  showItemCount?: boolean;
  disabled?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export function Pagination({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 25, 50, 100],
  showPageSizeSelector = true,
  showItemCount = true,
  disabled = false,
  size = 'medium',
}: PaginationProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    onPageChange(page);
  };

  const handlePageSizeChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const newPageSize = event.target.value as number;
    if (onPageSizeChange) {
      onPageSizeChange(newPageSize);
    }
  };

  if (totalPages <= 1 && !showPageSizeSelector) {
    return null;
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        alignItems: isMobile ? 'stretch' : 'center',
        justifyContent: 'space-between',
        gap: 2,
        py: 2,
      }}
    >
      {/* Item count and page size selector */}
      <Box
        sx={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: isMobile ? 'flex-start' : 'center',
          gap: 2,
        }}
      >
        {showItemCount && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ whiteSpace: 'nowrap' }}
          >
            Showing {startItem}-{endItem} of {totalItems} items
          </Typography>
        )}

        {showPageSizeSelector && onPageSizeChange && (
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="page-size-label">Items per page</InputLabel>
            <Select
              labelId="page-size-label"
              value={pageSize}
              onChange={handlePageSizeChange}
              label="Items per page"
              disabled={disabled}
            >
              {pageSizeOptions.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      </Box>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <MuiPagination
          count={totalPages}
          page={currentPage}
          onChange={handlePageChange}
          disabled={disabled}
          size={isMobile ? 'small' : size}
          showFirstButton={!isMobile}
          showLastButton={!isMobile}
          siblingCount={isMobile ? 0 : 1}
          boundaryCount={isMobile ? 1 : 2}
          renderItem={(item: any) => (
            <PaginationItem
              slots={{
                first: FirstPageIcon,
                last: LastPageIcon,
                previous: PrevIcon,
                next: NextIcon,
              }}
              {...item}
            />
          )}
          sx={{
            '& .MuiPaginationItem-root': {
              fontSize: size === 'small' ? '0.75rem' : '0.875rem',
            },
          }}
        />
      )}
    </Box>
  );
}

// Simple pagination for basic use cases
export interface SimplePaginationProps {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  onNext: () => void;
  onPrevious: () => void;
  loading?: boolean;
  nextLabel?: string;
  previousLabel?: string;
}

export function SimplePagination({
  hasNextPage,
  hasPreviousPage,
  onNext,
  onPrevious,
  loading = false,
  nextLabel = 'Next',
  previousLabel = 'Previous',
}: SimplePaginationProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        py: 2,
      }}
    >
      <Box>
        {hasPreviousPage && (
          <PaginationItem
            onClick={onPrevious}
            disabled={loading}
            type="previous"
            aria-label={previousLabel}
          >
            {previousLabel}
          </PaginationItem>
        )}
      </Box>

      <Box>
        {hasNextPage && (
          <PaginationItem
            onClick={onNext}
            disabled={loading}
            type="next"
            aria-label={nextLabel}
          >
            {nextLabel}
          </PaginationItem>
        )}
      </Box>
    </Box>
  );
}