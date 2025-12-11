import { describe, it, expect } from 'vitest';
import { isTokenExpired, hasRole, formatAuthError, createAuthenticatedUser } from '../auth';
import { User } from '../../types/auth';

describe('Auth Utilities', () => {
  describe('isTokenExpired', () => {
    it('should return true for expired token', () => {
      // Create a token that expired 1 hour ago
      const expiredTime = Math.floor(Date.now() / 1000) - 3600;
      const payload = { exp: expiredTime };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      expect(isTokenExpired(token)).toBe(true);
    });

    it('should return false for valid token', () => {
      // Create a token that expires in 1 hour
      const futureTime = Math.floor(Date.now() / 1000) + 3600;
      const payload = { exp: futureTime };
      const token = `header.${btoa(JSON.stringify(payload))}.signature`;
      
      expect(isTokenExpired(token)).toBe(false);
    });

    it('should return true for invalid token', () => {
      expect(isTokenExpired('invalid-token')).toBe(true);
    });
  });

  describe('hasRole', () => {
    const adminUser: User = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin',
      createdAt: '2023-01-01T00:00:00Z',
    };

    const regularUser: User = {
      id: 2,
      username: 'user',
      email: 'user@example.com',
      role: 'user',
      createdAt: '2023-01-01T00:00:00Z',
    };

    it('should return true for admin user with admin role requirement', () => {
      expect(hasRole(adminUser, 'admin')).toBe(true);
    });

    it('should return false for regular user with admin role requirement', () => {
      expect(hasRole(regularUser, 'admin')).toBe(false);
    });

    it('should return true for admin user with user role requirement', () => {
      expect(hasRole(adminUser, 'user')).toBe(true);
    });

    it('should return true for regular user with user role requirement', () => {
      expect(hasRole(regularUser, 'user')).toBe(true);
    });

    it('should return false for null user', () => {
      expect(hasRole(null, 'user')).toBe(false);
      expect(hasRole(null, 'admin')).toBe(false);
    });
  });

  describe('formatAuthError', () => {
    it('should format API error with detail', () => {
      const error = {
        response: {
          data: {
            detail: 'Invalid credentials',
          },
        },
      };
      
      expect(formatAuthError(error)).toBe('Invalid credentials');
    });

    it('should format 401 error', () => {
      const error = {
        response: {
          status: 401,
        },
      };
      
      expect(formatAuthError(error)).toBe('Invalid username or password');
    });

    it('should format 403 error', () => {
      const error = {
        response: {
          status: 403,
        },
      };
      
      expect(formatAuthError(error)).toBe('Access denied');
    });

    it('should format server error', () => {
      const error = {
        response: {
          status: 500,
        },
      };
      
      expect(formatAuthError(error)).toBe('Server error. Please try again later.');
    });

    it('should format generic error', () => {
      const error = {
        message: 'Network error',
      };
      
      expect(formatAuthError(error)).toBe('Network error');
    });

    it('should format unknown error', () => {
      const error = {};
      
      expect(formatAuthError(error)).toBe('An unexpected error occurred');
    });
  });

  describe('createAuthenticatedUser', () => {
    it('should create authenticated user with token', () => {
      const user: User = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'user',
        createdAt: '2023-01-01T00:00:00Z',
      };
      
      const token = 'test-token';
      const authenticatedUser = createAuthenticatedUser(user, token);
      
      expect(authenticatedUser).toEqual({
        ...user,
        token,
      });
    });
  });
});