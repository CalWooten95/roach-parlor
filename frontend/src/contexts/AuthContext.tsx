import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, AuthContextType, LoginCredentials, AuthenticatedUser } from '../types/auth';
import { authService, tokenStorage } from '../services/auth';
import { createAuthenticatedUser, formatAuthError } from '../utils/auth';

// Auth reducer actions
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: AuthenticatedUser }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN_SUCCESS'; payload: string }
  | { type: 'REFRESH_TOKEN_FAILURE' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

// Initial state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case 'REFRESH_TOKEN_SUCCESS':
      return {
        ...state,
        user: state.user ? { ...state.user, token: action.payload } : null,
        isLoading: false,
        error: null,
      };
    case 'REFRESH_TOKEN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: 'Session expired. Please log in again.',
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = tokenStorage.getToken();
      const user = tokenStorage.getUser();

      if (token && user) {
        // Check if token is expired
        if (authService.isTokenExpired(token)) {
          try {
            const newToken = await authService.refreshToken();
            tokenStorage.setToken(newToken);
            
            const authenticatedUser = createAuthenticatedUser(user, newToken);
            
            dispatch({ type: 'LOGIN_SUCCESS', payload: authenticatedUser });
          } catch (error) {
            // Refresh failed, clear storage
            tokenStorage.clearAll();
            dispatch({ type: 'REFRESH_TOKEN_FAILURE' });
          }
        } else {
          // Token is still valid
          const authenticatedUser = createAuthenticatedUser(user, token);
          
          dispatch({ type: 'LOGIN_SUCCESS', payload: authenticatedUser });
        }
      } else {
        // No token or user, set loading to false
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (credentials: LoginCredentials): Promise<void> => {
    dispatch({ type: 'LOGIN_START' });
    
    try {
      const response = await authService.login(credentials);
      
      // Store tokens and user data
      tokenStorage.setToken(response.access_token);
      tokenStorage.setUser(response.user);
      
      // Note: If your API provides refresh tokens, store them here
      // tokenStorage.setRefreshToken(response.refresh_token);
      
      const authenticatedUser = createAuthenticatedUser(response.user, response.access_token);
      
      dispatch({ type: 'LOGIN_SUCCESS', payload: authenticatedUser });
    } catch (error: any) {
      const errorMessage = formatAuthError(error);
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<void> => {
    try {
      const newToken = await authService.refreshToken();
      tokenStorage.setToken(newToken);
      dispatch({ type: 'REFRESH_TOKEN_SUCCESS', payload: newToken });
    } catch (error) {
      tokenStorage.clearAll();
      dispatch({ type: 'REFRESH_TOKEN_FAILURE' });
      throw error;
    }
  };

  // Clear error function
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    logout,
    refreshToken,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}