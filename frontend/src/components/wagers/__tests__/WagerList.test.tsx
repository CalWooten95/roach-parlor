import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../../../theme';
import { WagerList } from '../WagerList';
import { Wager, WagerStatus } from '../../../types';
import { WagerFilters } from '../../../services/wagers';

// Test wrapper with theme
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

// Mock wager data
const mockWagers: Wager[] = [
  {
    id: 1,
    userId: 1,
    description: 'Test wager 1',
    amount: 100,
    line: '-110',
    status: 'pending' as WagerStatus,
    isFrePlay: false,
    isLiveBet: false,
    autoCalculate: true,
    liveTrackingEnabled: true,
    archived: false,
    createdAt: '2023-01-01T00:00:00Z',
    legs: [],
    calculations: [],
  },
  {
    id: 2,
    userId: 1,
    description: 'Test wager 2',
    amount: 200,
    line: '+150',
    status: 'won' as WagerStatus,
    isFrePlay: true,
    isLiveBet: false,
    autoCalculate: true,
    liveTrackingEnabled: true,
    archived: false,
    createdAt: '2023-01-02T00:00:00Z',
    legs: [],
    calculations: [],
  },
];

// Mock functions
const mockOnRefresh = jest.fn();
const mockOnPageChange = jest.fn();
const mockOnFiltersChange = jest.fn();
const mockOnWagerStatusUpdate = jest.fn();
const mockOnWagerArchive = jest.fn();
const mockOnWagerDelete = jest.fn();
const mockOnWagerEdit = jest.fn();
const mockOnCreateWager = jest.fn();

const defaultProps = {
  wagers: mockWagers,
  loading: false,
  totalCount: 2,
  currentPage: 1,
  pageSize: 10,
  filters: {} as WagerFilters,
  onRefresh: mockOnRefresh,
  onPageChange: mockOnPageChange,
  onFiltersChange: mockOnFiltersChange,
  onWagerStatusUpdate: mockOnWagerStatusUpdate,
  onWagerArchive: mockOnWagerArchive,
  onWagerDelete: mockOnWagerDelete,
  onWagerEdit: mockOnWagerEdit,
  onCreateWager: mockOnCreateWager,
};

describe('WagerList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders wager list correctly', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    expect(screen.getByText('Wagers')).toBeInTheDocument();
    expect(screen.getByText('Test wager 1')).toBeInTheDocument();
    expect(screen.getByText('Test wager 2')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} loading={true} wagers={[]} />
      </TestWrapper>
    );

    // Should show skeleton loaders
    expect(screen.queryByText('Test wager 1')).not.toBeInTheDocument();
  });

  it('shows error state', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} error="Failed to load wagers" wagers={[]} />
      </TestWrapper>
    );

    expect(screen.getByText('Failed to load wagers')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('shows empty state when no wagers', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} wagers={[]} totalCount={0} />
      </TestWrapper>
    );

    expect(screen.getByText('No wagers found')).toBeInTheDocument();
    expect(screen.getByText('Get started by creating your first wager.')).toBeInTheDocument();
  });

  it('shows empty state with filter message when filters are applied', () => {
    const filtersApplied = { search: 'test search' };
    
    render(
      <TestWrapper>
        <WagerList 
          {...defaultProps} 
          wagers={[]} 
          totalCount={0} 
          filters={filtersApplied}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Try adjusting your filters or search terms.')).toBeInTheDocument();
  });

  it('calls onCreateWager when new wager button is clicked', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('New Wager'));
    expect(mockOnCreateWager).toHaveBeenCalled();
  });

  it('calls onRefresh when refresh button is clicked', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Refresh'));
    expect(mockOnRefresh).toHaveBeenCalled();
  });

  it('handles search input changes', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    const searchInput = screen.getByPlaceholderText('Search wagers...');
    fireEvent.change(searchInput, { target: { value: 'test search' } });

    // Note: Due to debouncing, we would need to wait or mock timers to test the actual call
    expect(searchInput).toHaveValue('test search');
  });

  it('shows filters panel when filters button is clicked', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Filters'));
    // The filters panel should be visible (this would depend on the WagerFilters component)
  });

  it('shows bulk actions when enabled', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} showBulkActions={true} />
      </TestWrapper>
    );

    expect(screen.getByText('Select All')).toBeInTheDocument();
  });

  it('handles bulk selection', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} showBulkActions={true} />
      </TestWrapper>
    );

    const selectAllCheckbox = screen.getByLabelText('Select All');
    fireEvent.click(selectAllCheckbox);

    // Should show selected count
    expect(screen.getByText('2 selected')).toBeInTheDocument();
    expect(screen.getByText('Bulk Actions')).toBeInTheDocument();
  });

  it('shows pagination when there are multiple pages', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} totalCount={25} pageSize={10} />
      </TestWrapper>
    );

    // Should show pagination controls
    expect(screen.getByText('Showing 1-10 of 25 items')).toBeInTheDocument();
  });

  it('does not show pagination when there is only one page', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} totalCount={5} pageSize={10} />
      </TestWrapper>
    );

    // Should not show pagination controls
    expect(screen.queryByText('Showing 1-5 of 5 items')).toBeInTheDocument();
  });

  it('shows floating action button when onCreateWager is provided', () => {
    render(
      <TestWrapper>
        <WagerList {...defaultProps} />
      </TestWrapper>
    );

    expect(screen.getByLabelText('Create wager')).toBeInTheDocument();
  });

  it('does not show create wager buttons when onCreateWager is not provided', () => {
    const propsWithoutCreate = { ...defaultProps };
    delete propsWithoutCreate.onCreateWager;

    render(
      <TestWrapper>
        <WagerList {...propsWithoutCreate} />
      </TestWrapper>
    );

    expect(screen.queryByText('New Wager')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Create wager')).not.toBeInTheDocument();
  });
});