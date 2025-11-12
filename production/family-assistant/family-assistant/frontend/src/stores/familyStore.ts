/**
 * Family members store using Zustand.
 *
 * Manages family member data with optimistic updates and error recovery.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { apiClient } from '../lib/api-client';

export interface FamilyMember {
  id: string;
  telegram_id?: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: string;
  age_group?: string;
  language_preference: string;
  active_skills: string[];
  privacy_level: string;
  safety_level: string;
  created_at: string;
  updated_at: string;
}

interface FamilyState {
  members: FamilyMember[];
  selectedMember: FamilyMember | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchMembers: () => Promise<void>;
  selectMember: (id: string) => void;
  updateMember: (id: string, data: Partial<FamilyMember>) => Promise<void>;
  deleteMember: (id: string) => Promise<void>;
  clearError: () => void;
}

export const useFamilyStore = create<FamilyState>()(
  devtools(
    immer((set, get) => ({
      members: [],
      selectedMember: null,
      isLoading: false,
      error: null,

      fetchMembers: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const response = await apiClient.get('/family/members');

          set((state) => {
            state.members = response.data;
            state.isLoading = false;
          });
        } catch (error: any) {
          const message = error.response?.data?.detail || 'Failed to fetch family members';

          set((state) => {
            state.error = message;
            state.isLoading = false;
          });

          throw new Error(message);
        }
      },

      selectMember: (id: string) => {
        set((state) => {
          state.selectedMember = state.members.find((m) => m.id === id) || null;
        });
      },

      updateMember: async (id: string, data: Partial<FamilyMember>) => {
        // Optimistic update
        const previousMembers = get().members;

        set((state) => {
          const index = state.members.findIndex((m) => m.id === id);
          if (index !== -1) {
            state.members[index] = { ...state.members[index], ...data };
          }
        });

        try {
          const response = await apiClient.put(`/family/members/${id}`, data);

          // Server reconciliation
          set((state) => {
            const index = state.members.findIndex((m) => m.id === id);
            if (index !== -1) {
              state.members[index] = response.data;
            }

            // Update selected member if it's the one being updated
            if (state.selectedMember?.id === id) {
              state.selectedMember = response.data;
            }
          });
        } catch (error: any) {
          // Rollback on failure
          set((state) => {
            state.members = previousMembers;
            state.error = error.response?.data?.detail || 'Failed to update member';
          });

          throw error;
        }
      },

      deleteMember: async (id: string) => {
        // Optimistic delete
        const previousMembers = get().members;

        set((state) => {
          state.members = state.members.filter((m) => m.id !== id);

          // Clear selected member if it's the one being deleted
          if (state.selectedMember?.id === id) {
            state.selectedMember = null;
          }
        });

        try {
          await apiClient.delete(`/family/members/${id}`);
        } catch (error: any) {
          // Rollback on failure
          set((state) => {
            state.members = previousMembers;
            state.error = error.response?.data?.detail || 'Failed to delete member';
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
    { name: 'FamilyStore' }
  )
);
