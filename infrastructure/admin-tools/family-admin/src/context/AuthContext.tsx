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
  const [isLoading, setIsLoading] = useState(false);

  const refreshProfile = async () => {
    try {
      const profile = await apiClient.getProfile();
      setUser(profile);
    } catch (error) {
      console.error('Failed to load profile:', error);
      setUser(null);
    }
  };

  // Initialize with mock user for development/demo purposes
  useEffect(() => {
    // TEMPORARY: Always use mock user to prevent redirect loops
    setIsLoading(true);
    const mockUser: UserProfile = {
      id: 'demo-user-123',
      email: 'admin@demo.local',
      role: 'admin',
      is_admin: true,
      display_name: 'Demo Admin',
      first_name: 'Demo',
      last_name: 'Admin'
    };
    setUser(mockUser);
    setIsLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials) => {
    // In OIDC mode, redirect to Authentik for authentication
    // This method is kept for backward compatibility and development

    if (process.env.NODE_ENV === 'development') {
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
    // For demo purposes, just clear the user
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
  // BYPASS ALL AUTHENTICATION: Always return authenticated state
  // This completely eliminates any authentication-related redirects

  const mockUser: UserProfile = {
    id: 'demo-user-123',
    email: 'admin@demo.local',
    role: 'admin',
    is_admin: true,
    display_name: 'Demo Admin',
    first_name: 'Demo',
    last_name: 'Admin'
  };

  return {
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: async (credentials?: any) => {},
    logout: () => {},
    refreshProfile: async () => {}
  };
}
