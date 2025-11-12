/**
 * Authentication store using Zustand.
 *
 * Manages user authentication state, login/logout, and token management.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { apiClient, setToken, clearToken, getToken } from '../lib/api-client';

export interface User {
  id: string;
  username: string;
  first_name: string;
  last_name?: string;
  role: string;
  telegram_id?: number;
  language_preference: string;
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      immer((set, get) => ({
        user: null,
        isAuthenticated: !!getToken(),
        isLoading: false,
        error: null,

        login: async (username: string, password: string) => {
          set((state) => {
            state.isLoading = true;
            state.error = null;
          });

          try {
            // Use OAuth2 password flow (form data)
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await apiClient.post('/auth/login', formData, {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            });

            const { access_token, expires_in } = response.data;

            // Store token
            setToken(access_token, expires_in);

            // Fetch user profile
            await get().fetchCurrentUser();

            set((state) => {
              state.isAuthenticated = true;
              state.isLoading = false;
            });
          } catch (error: any) {
            const message = error.response?.data?.detail || 'Login failed';

            set((state) => {
              state.isLoading = false;
              state.error = message;
              state.isAuthenticated = false;
            });

            throw new Error(message);
          }
        },

        logout: () => {
          clearToken();

          set((state) => {
            state.user = null;
            state.isAuthenticated = false;
            state.error = null;
          });
        },

        fetchCurrentUser: async () => {
          try {
            const response = await apiClient.get('/auth/me');

            set((state) => {
              state.user = response.data;
              state.isAuthenticated = true;
            });
          } catch (error: any) {
            console.error('Failed to fetch user:', error);

            set((state) => {
              state.user = null;
              state.isAuthenticated = false;
            });

            throw error;
          }
        },

        clearError: () => {
          set((state) => {
            state.error = null;
          });
        },
      })),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'AuthStore' }
  )
);
