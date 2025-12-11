import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute, AdminRoute } from './components/auth/ProtectedRoute';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Wagers } from './pages/Wagers';
import { LiveTracking } from './pages/LiveTracking';
import { Analytics } from './pages/Analytics';
import { Admin } from './pages/Admin';
import { NotFound } from './pages/NotFound';

function App() {
  return (
    <AuthProvider>
      <AppLayout>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/wagers"
            element={
              <ProtectedRoute>
                <Wagers />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/live"
            element={
              <ProtectedRoute>
                <LiveTracking />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />
          
          {/* Admin-only routes */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <Admin />
              </AdminRoute>
            }
          />
          
          {/* 404 route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AppLayout>
    </AuthProvider>
  );
}

export default App;