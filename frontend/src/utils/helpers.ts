import { WagerStatus } from '@/types';

// Format currency values
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

// Format date strings
export const formatDate = (dateString: string): string => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(dateString));
};

// Format relative time (e.g., "2 hours ago")
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
};

// Get status color for Material-UI
export const getStatusColor = (status: WagerStatus): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (status) {
    case 'won':
      return 'success';
    case 'lost':
      return 'error';
    case 'push':
      return 'info';
    case 'cancelled':
      return 'warning';
    case 'pending':
    default:
      return 'default';
  }
};

// Calculate potential payout
export const calculatePayout = (amount: number, line: string): number | null => {
  // Basic calculation for American odds format
  const odds = parseFloat(line.replace(/[^-\d.]/g, ''));
  
  if (isNaN(odds)) {
    return null;
  }

  if (odds > 0) {
    // Positive odds: (odds / 100) * amount
    return (odds / 100) * amount;
  } else {
    // Negative odds: (100 / Math.abs(odds)) * amount
    return (100 / Math.abs(odds)) * amount;
  }
};

// Validate email format
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Debounce function for search inputs
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// Generate unique ID for temporary items
export const generateTempId = (): string => {
  return `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Parse betting line to extract odds
export const parseBettingLine = (line: string): { odds: number; type: string } | null => {
  // Simple parser for common betting line formats
  const americanOddsMatch = line.match(/([+-]?\d+)/);
  
  if (americanOddsMatch) {
    return {
      odds: parseInt(americanOddsMatch[1]),
      type: 'american',
    };
  }

  return null;
};