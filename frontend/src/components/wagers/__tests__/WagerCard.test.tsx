import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../../../theme';
import { WagerCard } from '../WagerCard';
import { Wager, WagerStatus } from '../../../types';

// Test wrapper with theme
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

// Mock wager data
const mockWager: Wager = {
  id: 1,
  userId: 1,
  description: 'Test wager description',
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
};

// Mock functions
const mockOnStatusUpdate = jest.fn();
const mockOnArchive = jest.fn();
const mockOnDelete = jest.fn();
const mockOnEdit = jest.fn();

describe('WagerCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders wager information correctly', () => {
    render(
      <TestWrapper>
        <WagerCard
          wager={mockWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Test wager description')).toBeInTheDocument();
    expect(screen.getByText('$100.00')).toBeInTheDocument();
    expect(screen.getByText('-110')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('shows free play chip when isFrePlay is true', () => {
    const freePlayWager = { ...mockWager, isFrePlay: true };
    
    render(
      <TestWrapper>
        <WagerCard
          wager={freePlayWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Free Play')).toBeInTheDocument();
  });

  it('shows live bet chip when isLiveBet is true', () => {
    const liveBetWager = { ...mockWager, isLiveBet: true };
    
    render(
      <TestWrapper>
        <WagerCard
          wager={liveBetWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Live Bet')).toBeInTheDocument();
  });

  it('shows archived chip when archived is true', () => {
    const archivedWager = { ...mockWager, archived: true };
    
    render(
      <TestWrapper>
        <WagerCard
          wager={archivedWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Archived')).toBeInTheDocument();
  });

  it('displays matchup information when available', () => {
    const wagerWithMatchup = {
      ...mockWager,
      matchup: {
        id: 1,
        homeTeam: 'Home Team',
        awayTeam: 'Away Team',
        league: 'NFL',
        scheduledTime: '2023-01-01T20:00:00Z',
      },
    };

    render(
      <TestWrapper>
        <WagerCard
          wager={wagerWithMatchup}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Away Team @ Home Team')).toBeInTheDocument();
    expect(screen.getByText('NFL')).toBeInTheDocument();
  });

  it('displays legs when available', () => {
    const wagerWithLegs = {
      ...mockWager,
      legs: [
        {
          id: 1,
          wagerId: 1,
          description: 'Leg 1 description',
          status: 'pending' as WagerStatus,
          createdAt: '2023-01-01T00:00:00Z',
        },
        {
          id: 2,
          wagerId: 1,
          description: 'Leg 2 description',
          status: 'won' as WagerStatus,
          createdAt: '2023-01-01T00:00:00Z',
        },
      ],
    };

    render(
      <TestWrapper>
        <WagerCard
          wager={wagerWithLegs}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Legs (2)')).toBeInTheDocument();
    expect(screen.getByText('Leg 1 description')).toBeInTheDocument();
    expect(screen.getByText('Leg 2 description')).toBeInTheDocument();
  });

  it('shows update status button for active wagers', () => {
    render(
      <TestWrapper>
        <WagerCard
          wager={mockWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Update Status')).toBeInTheDocument();
  });

  it('does not show update status button for archived wagers', () => {
    const archivedWager = { ...mockWager, archived: true };
    
    render(
      <TestWrapper>
        <WagerCard
          wager={archivedWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    expect(screen.queryByText('Update Status')).not.toBeInTheDocument();
  });

  it('calls onStatusUpdate when status is changed', () => {
    render(
      <TestWrapper>
        <WagerCard
          wager={mockWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
        />
      </TestWrapper>
    );

    // Click update status button
    fireEvent.click(screen.getByText('Update Status'));
    
    // Click won option
    fireEvent.click(screen.getByText('Won'));

    expect(mockOnStatusUpdate).toHaveBeenCalledWith(1, 'won');
  });

  it('hides actions when showActions is false', () => {
    render(
      <TestWrapper>
        <WagerCard
          wager={mockWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
          showActions={false}
        />
      </TestWrapper>
    );

    expect(screen.queryByLabelText('Wager actions')).not.toBeInTheDocument();
  });

  it('shows loading state when loading is true', () => {
    render(
      <TestWrapper>
        <WagerCard
          wager={mockWager}
          onStatusUpdate={mockOnStatusUpdate}
          onArchive={mockOnArchive}
          onDelete={mockOnDelete}
          loading={true}
        />
      </TestWrapper>
    );

    // Actions should be disabled when loading
    const actionsButton = screen.queryByLabelText('Wager actions');
    if (actionsButton) {
      expect(actionsButton).toBeDisabled();
    }
  });
});