/**
 * Protected Route Component
 *
 * Provides route protection for authenticated users only.
 * Redirects unauthenticated users to login page.
 */

import React, { useEffect, ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAdmin?: boolean;
  requireParent?: boolean;
  redirectTo?: string;
  loadingComponent?: ReactNode;
}

export function ProtectedRoute({
  children,
  requireAdmin = false,
  requireParent = false,
  redirectTo = '/login',
  loadingComponent,
}: ProtectedRouteProps) {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Show loading component while checking authentication
  if (isLoading) {
    return loadingComponent || (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Save the attempted location for redirect after login
    const returnTo = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`${redirectTo}?returnTo=${returnTo}`} replace />;
  }

  // Check admin requirements
  if (requireAdmin && !user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full text-center p-8">
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 mb-6">
            <svg
              className="mx-auto h-12 w-12 text-yellow-600 dark:text-yellow-400 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.932-3.334.285-1.667.33-3.333-.33-3.333l-7.26 4.667a1 1 0 01-1.932-.334l-7.26-4.667C1.667 5.667 2.502 4 4.044 4zm-.006 7.666V10a4 4 0 114 0z"
              />
            </svg>
            <h2 className="text-lg font-medium text-yellow-800 dark:text-yellow-200 mb-2">
              Admin Access Required
            </h2>
            <p className="text-yellow-700 dark:text-yellow-300">
              This page requires administrator privileges. You don't have permission to access this resource.
            </p>
          </div>
          <button
            onClick={() => window.history.back()}
            className="bg-yellow-600 hover:bg-yellow-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Check parent requirements
  if (requireParent) {
    const isParent = user?.role === 'parent' || user?.role === 'grandparent';
    if (!isParent) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full text-center p-8">
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-6">
              <svg
                className="mx-auto h-12 w-12 text-blue-600 dark:text-blue-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0H15a4.996 4.996 0 011.928-2.643M7 16a4.996 4.996 0 01-1.928-2.643M3 4a5 5 0 015-2.643 5.924M7 16H3a5 5 0 01-2.643-5.924M17 16a5 5 0 001.928-2.643M7 4a5.995 5.995 0 00-5.924 6M17 4a5.995 5.995 0 005.924 6M7 16v-2m0-4V6M7 4v2m0 4v2"
                />
              </svg>
              <h2 className="text-lg font-medium text-blue-800 dark:text-blue-200 mb-2">
                Parent Access Required
              </h2>
              <p className="text-blue-700 dark:text-blue-300">
                This page requires parent or grandparent privileges. Your current role doesn't have access to this resource.
              </p>
              <div className="mt-3 text-sm text-blue-600 dark:text-blue-400">
                Current role: <span className="font-semibold capitalize">{user?.role}</span>
              </div>
            </div>
            <button
              onClick={() => window.history.back()}
              className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // User is authenticated and has required permissions
  return <>{children}</>;
}

// =============================================================================
// Permission-based Components
// =============================================================================

interface RequirePermissionProps {
  permission: string;
  resource?: string;
  action?: string;
  fallback?: ReactNode;
  children: ReactNode;
}

export function RequirePermission({
  permission,
  resource,
  action,
  fallback,
  children,
}: RequirePermissionProps) {
  const { user } = useAuth();

  // Check if user has required permission
  const hasPermission = (): boolean => {
    if (!user) return false;
    if (user.is_admin) return true; // Admins have all permissions

    // Define role permissions (should match backend)
    const rolePermissions: Record<string, string[]> = {
      parent: [
        'read:own_data', 'write:own_data', 'read:family_data', 'write:family_data',
        'manage_children', 'view_analytics', 'manage_settings', 'approve_content',
        'read:sibling_data', 'chat:ai', 'games:play'
      ],
      grandparent: [
        'read:own_data', 'write:own_data', 'read:family_data',
        'view_analytics', 'read:sibling_data', 'chat:ai'
      ],
      teenager: [
        'read:own_data', 'write:own_data', 'read:sibling_data', 'chat:ai'
      ],
      child: [
        'read:own_data', 'chat:ai', 'games:play'
      ],
      member: [
        'read:own_data', 'write:own_data', 'chat:ai'
      ],
    };

    const permissions = rolePermissions[user.role] || [];
    return permissions.includes(permission);
  };

  if (!hasPermission()) {
    return (
      <>{fallback || (
        <div className="flex items-center justify-center min-h-24 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            You don't have permission to access this content.
          </p>
        </div>
      )}</>
    );
  }

  return <>{children}</>;
}

// =============================================================================
// Role-based Components
// =============================================================================

interface RequireRoleProps {
  roles: string[];
  fallback?: ReactNode;
  children: ReactNode;
}

export function RequireRole({ roles, fallback, children }: RequireRoleProps) {
  const { user } = useAuth();

  const hasRequiredRole = user && roles.includes(user.role);

  if (!hasRequiredRole) {
    return (
      <>{fallback || (
        <div className="flex items-center justify-center min-h-24 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            Access restricted. Required roles: {roles.join(', ')}.
          </p>
        </div>
      )}</>
    );
  }

  return <>{children}</>;
}

// =============================================================================
// Exported permission components
// =============================================================================

export function RequireAdmin({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RequireRole roles={['parent']} fallback={fallback}>
      <RequirePermission permission="manage_settings" fallback={fallback}>
        {children}
      </RequirePermission>
    </RequireRole>
  );
}

export function RequireParent({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RequireRole roles={['parent', 'grandparent']} fallback={fallback}>
      {children}
    </RequireRole>
  );
}