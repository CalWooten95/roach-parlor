import { AuthenticatedUser, User } from '../types/auth';

/**
 * Utility functions for authentication
 */

export const AUTH_STORAGE_KEYS = {
  TOKEN: 'roach_parlor_token',
  REFRESH_TOKEN: 'roach_parlor_refresh_token',
  USER: 'roach_parlor_user',
} as const;

/**
 * Check if a JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch (error) {
    return true;
  }
}

/**
 * Get token expiration time
 */
export function getTokenExpiration(token: string): Date | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return new Date(payload.exp * 1000);
  } catch (error) {
    return null;
  }
}

/**
 * Check if user has required role
 */
export function hasRole(user: User | AuthenticatedUser | null, requiredRole: 'user' | 'admin'): boolean {
  if (!user) return false;
  
  if (requiredRole === 'admin') {
    return user.role === 'admin';
  }
  
  return user.role === 'user' || user.role === 'admin';
}

/**
 * Format authentication error messages
 */
export function formatAuthError(error: any): string {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  if (error.response?.status === 401) {
    return 'Invalid username or password';
  }
  
  if (error.response?.status === 403) {
    return 'Access denied';
  }
  
  if (error.response?.status >= 500) {
    return 'Server error. Please try again later.';
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Create authenticated user object
 */
export function createAuthenticatedUser(user: User, token: string): AuthenticatedUser {
  return {
    ...user,
    token,
  };
}