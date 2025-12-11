import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { theme } from '../../../theme';
import { Button } from '../Button';

// Test wrapper with theme
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={theme}>{children}</ThemeProvider>
);

describe('Button Component', () => {
  it('renders button with text', () => {
    render(
      <TestWrapper>
        <Button>Click me</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    
    render(
      <TestWrapper>
        <Button onClick={handleClick}>Click me</Button>
      </TestWrapper>
    );
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(
      <TestWrapper>
        <Button loading>Loading button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(
      <TestWrapper>
        <Button disabled>Disabled button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('has proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <Button aria-label="Custom label">Button</Button>
      </TestWrapper>
    );
    
    expect(screen.getByRole('button', { name: /custom label/i })).toBeInTheDocument();
  });
});