"use client";

import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Redirect to Authentik for authentication if not authenticated
  if (!isAuthenticated || !user) {
    // Redirect to Authentik for authentication
    const authUrl = new URL('https://auth.pesulabs.net/application/o/authorize');
    authUrl.searchParams.set('client_id', process.env.NEXT_PUBLIC_AUTHENTIK_CLIENT_ID || '');
    authUrl.searchParams.set('redirect_uri', window.location.origin);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', 'openid profile email');

    window.location.href = authUrl.toString();
    return null;
  }

  // Check if user has admin privileges
  if (!user.is_admin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">You need administrator privileges to access this page.</p>
        </div>
      </div>
    );
  }

  // User is authenticated and has admin privileges
  return <>{children}</>;
}