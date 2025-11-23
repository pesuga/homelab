"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function SSOSignIn() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    // If already authenticated, redirect to dashboard
    if (user && !isLoading) {
      router.push('/dashboard');
      return;
    }
  }, [user, isLoading, router]);

  // Show loading state
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="text-center">
        <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto"></div>
        <p className="text-gray-600 dark:text-gray-400">
          {isLoading ? 'Loading...' : 'Demo Authentication Active'}
        </p>
        <p className="mt-2 text-sm text-green-600 dark:text-green-400">
          Welcome to the Family Admin Dashboard
        </p>
      </div>
    </div>
  );
}