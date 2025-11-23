"use client";

// TEMPORARILY DISABLED: ProtectedRoute component to prevent redirect loops
// This component was causing infinite redirects by checking authentication
// and redirecting unauthenticated users to signin page

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // For now, just render children without any authentication checks
  return <>{children}</>;
}