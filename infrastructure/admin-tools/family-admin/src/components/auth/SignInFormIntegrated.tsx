"use client";

import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function SignInFormIntegrated() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();

  // Since we've bypassed authentication, check if user exists and redirect
  if (!isLoading && isAuthenticated) {
    router.replace('/dashboard');
  }

  // Show loading state
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="text-center">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
        <p className="text-gray-600 dark:text-gray-400">
          {isLoading ? 'Checking authentication...' : 'Development Mode - Bypassing Login'}
        </p>
        <p className="mt-2 text-sm text-green-600 dark:text-green-400">
          Redirecting to dashboard...
        </p>
      </div>
    </div>
  );
}