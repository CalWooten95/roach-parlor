# Authentication System

This directory contains the authentication infrastructure for the React frontend.

## Components

### AuthContext
- Provides authentication state management using React Context and useReducer
- Handles login, logout, and token refresh operations
- Manages session persistence and automatic token refresh
- Provides loading states and error handling

### ProtectedRoute
- Higher-order component for protecting routes that require authentication
- Supports role-based access control (user/admin)
- Redirects unauthenticated users to login page
- Shows loading spinner during authentication check

### LoginForm
- Complete login form with validation
- Integrates with AuthContext for authentication
- Handles form submission and error display
- Redirects to intended destination after successful login

### LogoutButton
- Provides logout functionality with menu or button variants
- Shows user information and role
- Handles logout process with loading states

## Services

### authService
- Handles all API communication for authentication
- Manages JWT tokens and automatic refresh
- Provides axios interceptors for token management
- Handles token expiration and refresh logic

### tokenStorage
- Manages localStorage operations for tokens and user data
- Provides consistent storage keys
- Handles token retrieval and cleanup

## Types

### AuthState
- Defines the shape of authentication state
- Includes user, loading, error, and authentication status

### AuthContextType
- Defines the authentication context interface
- Includes all state and action methods

### LoginCredentials
- Defines login form data structure

### User/AuthenticatedUser
- Defines user data structures with and without tokens

## Usage

### Protecting Routes
```tsx
import { ProtectedRoute, AdminRoute } from './components/auth';

// Protect any authenticated route
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

// Protect admin-only route
<AdminRoute>
  <AdminPanel />
</AdminRoute>
```

### Using Authentication Context
```tsx
import { useAuth } from './contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  // Use authentication state and methods
}
```

### Login Flow
1. User enters credentials in LoginForm
2. Form validates input and calls authService.login()
3. Service makes API request to backend
4. On success, tokens are stored and user is authenticated
5. User is redirected to intended destination
6. AuthContext provides authentication state to entire app

### Token Management
- JWT tokens are stored in localStorage
- Automatic refresh when tokens expire
- Axios interceptors handle token attachment and refresh
- Tokens are cleared on logout or refresh failure

## Security Features

- JWT token expiration checking
- Automatic token refresh
- Role-based access control
- Secure token storage
- Request/response interceptors
- Error handling and user feedback
- Session persistence across browser sessions

## Requirements Satisfied

This implementation satisfies the following requirements:

- **1.4**: Client-side navigation with React Router
- **6.5**: Role-based access control enforcement  
- **4.1**: Clean API communication separation
- **4.2**: WebSocket authentication (prepared for)
- **8.4**: Automatic reconnection and error handling