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
      const profile = await apiClient.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Failed to load profile:', error);
      // If profile fetch fails, clear token (might be expired)
      apiClient.clearToken();
      setUser(null);
    }
  };

  // Check for existing token on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = apiClient.getToken();

      // Development bypass: allow access without authentication
      if (process.env.NODE_ENV === 'development') {
        console.log('🚀 Development mode: Bypassing authentication for testing');
        setUser({
          id: 'dev-admin',
          email: 'admin@dev.local',
          role: 'admin',
          is_admin: true,
          display_name: 'Development Admin',
          first_name: 'Development',
          last_name: 'Admin'
        });
        setIsLoading(false);
        return;
      }

      if (token) {
        await refreshProfile();
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    // Development bypass: allow any login
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 Development mode: Bypassing login');
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

    try {
      await apiClient.login(credentials);
      await refreshProfile();
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 Development mode: Bypassing logout');
      setUser(null);
      return;
    }

    apiClient.logout();
    setUser(null);
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
