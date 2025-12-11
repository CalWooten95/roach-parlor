# Wager Components

This directory contains React components for wager display and management functionality.

## Components

### WagerCard
A card component that displays individual wager information with actions.

**Props:**
- `wager`: Wager object containing all wager data
- `onStatusUpdate`: Function to handle wager status updates
- `onArchive`: Function to handle archiving/unarchiving wagers
- `onDelete`: Function to handle wager deletion
- `onEdit`: Optional function to handle wager editing
- `showActions`: Boolean to show/hide action buttons
- `loading`: Boolean to show loading state

**Features:**
- Displays wager description, amount, line, and status
- Shows chips for free play, live bet, and archived status
- Displays matchup information when available
- Shows wager legs for parlay bets
- Provides status update menu for active wagers
- Shows live score data when available
- Responsive design with proper accessibility

### WagerList
A list component that displays multiple wagers with filtering, sorting, and pagination.

**Props:**
- `wagers`: Array of wager objects to display
- `loading`: Boolean loading state
- `error`: Optional error message
- `totalCount`: Total number of wagers for pagination
- `currentPage`: Current page number
- `pageSize`: Number of items per page
- `filters`: Current filter settings
- `onRefresh`: Function to refresh the wager list
- `onPageChange`: Function to handle page changes
- `onFiltersChange`: Function to handle filter changes
- `onWagerStatusUpdate`: Function to handle status updates
- `onWagerArchive`: Function to handle archiving
- `onWagerDelete`: Function to handle deletion
- `onWagerEdit`: Optional function to handle editing
- `onCreateWager`: Optional function to create new wagers
- `showBulkActions`: Boolean to enable bulk operations

**Features:**
- Grid layout with responsive design
- Search functionality with debouncing
- Advanced filtering panel
- Bulk selection and operations
- Pagination with page size options
- Empty states for no data and errors
- Floating action button for quick access
- Loading skeletons

### WagerFilters
A collapsible filter panel for advanced wager filtering.

**Props:**
- `filters`: Current filter settings
- `onFiltersChange`: Function to handle filter changes
- `onClose`: Function to close the filter panel

**Features:**
- Status filtering with chips
- Archive status filtering
- Date range selection
- Sorting options
- Clear all filters functionality
- Responsive design

### WagerDetail
A detailed view component for individual wagers.

**Props:**
- `wager`: Wager object to display
- `onStatusUpdate`: Function to handle status updates
- `onArchive`: Function to handle archiving
- `onDelete`: Function to handle deletion
- `onEdit`: Optional function to handle editing
- `onClose`: Optional function to close the detail view
- `loading`: Boolean loading state

**Features:**
- Comprehensive wager information display
- Matchup details with team information
- Live data display (scores, odds)
- Wager legs table for parlays
- Calculation history table
- Action buttons for status management
- Responsive layout

## Services

### wagerService
API service for wager-related operations.

**Methods:**
- `getWagers(params)`: Get paginated list of wagers
- `getWager(id)`: Get single wager by ID
- `createWager(wager)`: Create new wager
- `updateWager(id, updates)`: Update existing wager
- `updateWagerStatus(id, status)`: Update wager status
- `archiveWager(id, archived)`: Archive/unarchive wager
- `deleteWager(id)`: Delete wager
- `bulkUpdateStatus(ids, status)`: Bulk status update
- `bulkArchive(ids, archived)`: Bulk archive operation
- `bulkDelete(ids)`: Bulk delete operation

## Hooks

### useWagers
React Query hooks for wager management.

**Available hooks:**
- `useWagers(params)`: Fetch paginated wagers
- `useWager(id)`: Fetch single wager
- `useCreateWager()`: Create wager mutation
- `useUpdateWager()`: Update wager mutation
- `useUpdateWagerStatus()`: Update status mutation
- `useArchiveWager()`: Archive wager mutation
- `useDeleteWager()`: Delete wager mutation
- `useBulkUpdateStatus()`: Bulk status update mutation
- `useBulkArchive()`: Bulk archive mutation
- `useBulkDelete()`: Bulk delete mutation

## Usage Example

```tsx
import React, { useState } from 'react';
import { WagerList } from '@/components/wagers';
import { useWagers, useUpdateWagerStatus } from '@/hooks/useWagers';
import { WagerFilters } from '@/services/wagers';

export function WagersPage() {
  const [filters, setFilters] = useState<WagerFilters>({
    archived: false,
    sortBy: 'createdAt',
    sortOrder: 'desc',
  });
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, error, refetch } = useWagers({
    ...filters,
    page: currentPage,
    pageSize: 12,
  });

  const updateStatusMutation = useUpdateWagerStatus();

  const handleStatusUpdate = async (wagerId: number, status: WagerStatus) => {
    await updateStatusMutation.mutateAsync({ id: wagerId, status });
  };

  return (
    <WagerList
      wagers={data?.data || []}
      loading={isLoading}
      error={error?.message}
      totalCount={data?.total || 0}
      currentPage={currentPage}
      pageSize={12}
      filters={filters}
      onRefresh={refetch}
      onPageChange={setCurrentPage}
      onFiltersChange={setFilters}
      onWagerStatusUpdate={handleStatusUpdate}
      // ... other handlers
    />
  );
}
```

## Testing

The components include comprehensive test suites using Jest and React Testing Library:

- `WagerCard.test.tsx`: Tests for wager card component
- `WagerList.test.tsx`: Tests for wager list component

Run tests with:
```bash
npm test -- --testPathPattern=wagers
```

## Accessibility

All components follow accessibility best practices:
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- High contrast support
- Focus management

## Performance

Components are optimized for performance:
- React.memo for preventing unnecessary re-renders
- Debounced search input
- Virtualization for large lists (when needed)
- Efficient React Query caching
- Lazy loading of images and heavy components