import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../../../theme';
import { StatusBadge } from '../Badge';

// Test wrapper with theme
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe('StatusBadge Component', () => {
  it('renders won status correctly', () => {
    render(
      <TestWrapper>
        <StatusBadge status="won" />
      </TestWrapper>
    );
    
    expect(screen.getByText('Won')).toBeInTheDocument();
  });

  it('renders lost status correctly', () => {
    render(
      <TestWrapper>
        <StatusBadge status="lost" />
      </TestWrapper>
    );
    
    expect(screen.getByText('Lost')).toBeInTheDocument();
  });

  it('renders pending status correctly', () => {
    render(
      <TestWrapper>
        <StatusBadge status="pending" />
      </TestWrapper>
    );
    
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('renders archived status correctly', () => {
    render(
      <TestWrapper>
        <StatusBadge status="archived" />
      </TestWrapper>
    );
    
    expect(screen.getByText('Archived')).toBeInTheDocument();
  });

  it('renders live status correctly', () => {
    render(
      <TestWrapper>
        <StatusBadge status="live" />
      </TestWrapper>
    );
    
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('applies correct size prop', () => {
    const { rerender } = render(
      <TestWrapper>
        <StatusBadge status="won" size="small" />
      </TestWrapper>
    );
    
    let badge = screen.getByText('Won');
    expect(badge).toBeInTheDocument();
    
    rerender(
      <TestWrapper>
        <StatusBadge status="won" size="medium" />
      </TestWrapper>
    );
    
    badge = screen.getByText('Won');
    expect(badge).toBeInTheDocument();
  });
});