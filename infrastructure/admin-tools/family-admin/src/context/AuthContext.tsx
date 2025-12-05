"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, LoginCredentials, UserProfile } from '@/lib/api-client';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = async () => {
    try {
      const response = await fetch('/api/auth/me');
      if (response.ok) {
        const profile = await response.json();
        setUser(profile);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Check authentication status on mount
  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    // In production with Authentik, login is handled by SSO
    // This method is only used for development with bypass enabled

    if (process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true') {
      console.log('🚀 Development mode: Simulating login');
      setUser({
        id: 'dev-admin',
        email: credentials.email,
        role: 'admin',
        is_admin: true,
        display_name: 'Development Admin',
        first_name: 'Development',
        last_name: 'Admin'
      });
      return;
    }

    throw new Error('Login is handled by Authentik SSO. Please access the application through the authenticated URL.');
  };

  const logout = () => {
    // Clear user state - in production, this would redirect to Authentik logout
    setUser(null);
    window.location.href = 'https://auth.pesulabs.net/application/o/authorize?redirect_uri=' + encodeURIComponent(window.location.origin);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
