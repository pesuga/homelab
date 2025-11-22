/**
 * Custom hook for managing family data with Phase 2 backend integration
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, FamilyMember, ParentalControls, ActivityReport } from '@/lib/api-client';

interface UseFamilyDataReturn {
  // Family Members
  members: FamilyMember[];
  membersLoading: boolean;
  membersError: string | null;
  fetchMembers: () => Promise<void>;
  createMember: (member: Partial<FamilyMember>) => Promise<void>;
  updateMember: (id: string, updates: Partial<FamilyMember>) => Promise<void>;
  deleteMember: (id: string) => Promise<void>;

  // Parental Controls
  controls: Record<string, ParentalControls>;
  controlsLoading: boolean;
  controlsError: string | null;
  fetchControls: (memberId: string) => Promise<void>;
  updateControls: (memberId: string, controls: ParentalControls) => Promise<void>;

  // Activity Reports
  reports: ActivityReport[];
  reportsLoading: boolean;
  reportsError: string | null;
  fetchReports: (startDate?: string, endDate?: string) => Promise<void>;
  fetchUserReport: (userId: string, startDate?: string, endDate?: string) => Promise<void>;
}

export function useFamilyData(): UseFamilyDataReturn {
  // Family Members state
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [membersError, setMembersError] = useState<string | null>(null);

  // Parental Controls state
  const [controls, setControls] = useState<Record<string, ParentalControls>>({});
  const [controlsLoading, setControlsLoading] = useState(false);
  const [controlsError, setControlsError] = useState<string | null>(null);

  // Activity Reports state
  const [reports, setReports] = useState<ActivityReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);

  // ============================================================================
  // Family Members Operations
  // ============================================================================

  const fetchMembers = useCallback(async () => {
    setMembersLoading(true);
    setMembersError(null);
    try {
      const data = await apiClient.getFamilyMembers();
      setMembers(data);
    } catch (error) {
      // Temporary mock data for development while backend connectivity is resolved
      console.warn('Backend not accessible, using mock data:', error);
      const mockData: FamilyMember[] = [
        {
          id: '1',
          name: 'John Doe',
          email: 'john@family.local',
          role: 'parent',
          avatar: '',
          language_preference: 'en',
          parental_controls: {
            safe_search: true,
            content_filter: 'moderate',
            screen_time_daily: 120,
            screen_time_weekend: 180,
            allowed_apps: ['games', 'education'],
            blocked_keywords: ['violence', 'adult']
          },
          created_at: '2025-01-01T00:00:00Z',
          last_active: '2025-01-20T12:00:00Z'
        },
        {
          id: '2',
          name: 'Jane Doe',
          email: 'jane@family.local',
          role: 'parent',
          avatar: '',
          language_preference: 'en',
          parental_controls: {
            safe_search: true,
            content_filter: 'moderate',
            screen_time_daily: 120,
            screen_time_weekend: 180,
            allowed_apps: ['social', 'education'],
            blocked_keywords: ['spam', 'adult']
          },
          created_at: '2025-01-01T00:00:00Z',
          last_active: '2025-01-20T10:30:00Z'
        },
        {
          id: '3',
          name: 'Tommy Doe',
          email: 'tommy@family.local',
          role: 'child',
          avatar: '',
          language_preference: 'en',
          parental_controls: {
            safe_search: true,
            content_filter: 'strict',
            screen_time_daily: 90,
            screen_time_weekend: 120,
            allowed_apps: ['games', 'education', 'cartoons'],
            blocked_keywords: ['violence', 'adult', 'scary']
          },
          created_at: '2025-01-05T00:00:00Z',
          last_active: '2025-01-20T15:45:00Z'
        },
        {
          id: '4',
          name: 'Susie Doe',
          email: 'susie@family.local',
          role: 'teenager',
          avatar: '',
          language_preference: 'en',
          parental_controls: {
            safe_search: true,
            content_filter: 'moderate',
            screen_time_daily: 150,
            screen_time_weekend: 200,
            allowed_apps: ['social', 'games', 'education', 'music'],
            blocked_keywords: ['adult']
          },
          created_at: '2025-01-08T00:00:00Z',
          last_active: '2025-01-20T16:20:00Z'
        }
      ];
      setMembers(mockData);
      setMembersError('Using mock data - backend connection unavailable');
    } finally {
      setMembersLoading(false);
    }
  }, []);

  const createMember = useCallback(async (member: Partial<FamilyMember>) => {
    setMembersLoading(true);
    setMembersError(null);
    try {
      const newMember = await apiClient.createFamilyMember(member);
      setMembers(prev => [...prev, newMember]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create family member';
      setMembersError(message);
      throw error;
    } finally {
      setMembersLoading(false);
    }
  }, []);

  const updateMember = useCallback(async (id: string, updates: Partial<FamilyMember>) => {
    setMembersLoading(true);
    setMembersError(null);
    try {
      const updatedMember = await apiClient.updateFamilyMember(id, updates);
      setMembers(prev => prev.map(m => m.id === id ? updatedMember : m));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update family member';
      setMembersError(message);
      throw error;
    } finally {
      setMembersLoading(false);
    }
  }, []);

  const deleteMember = useCallback(async (id: string) => {
    setMembersLoading(true);
    setMembersError(null);
    try {
      await apiClient.deleteFamilyMember(id);
      setMembers(prev => prev.filter(m => m.id !== id));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete family member';
      setMembersError(message);
      throw error;
    } finally {
      setMembersLoading(false);
    }
  }, []);

  // ============================================================================
  // Parental Controls Operations
  // ============================================================================

  const fetchControls = useCallback(async (memberId: string) => {
    setControlsLoading(true);
    setControlsError(null);
    try {
      const data = await apiClient.getParentalControls(memberId);
      setControls(prev => ({ ...prev, [memberId]: data }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch parental controls';
      setControlsError(message);
      console.error('Error fetching parental controls:', error);
    } finally {
      setControlsLoading(false);
    }
  }, []);

  const updateControls = useCallback(async (memberId: string, newControls: ParentalControls) => {
    setControlsLoading(true);
    setControlsError(null);
    try {
      await apiClient.updateParentalControls(memberId, newControls);
      setControls(prev => ({ ...prev, [memberId]: newControls }));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update parental controls';
      setControlsError(message);
      throw error;
    } finally {
      setControlsLoading(false);
    }
  }, []);

  // ============================================================================
  // Activity Reports Operations
  // ============================================================================

  const fetchReports = useCallback(async (startDate?: string, endDate?: string) => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const data = await apiClient.getActivityReports(startDate, endDate);
      setReports(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch activity reports';
      setReportsError(message);
      console.error('Error fetching activity reports:', error);
    } finally {
      setReportsLoading(false);
    }
  }, []);

  const fetchUserReport = useCallback(async (userId: string, startDate?: string, endDate?: string) => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const data = await apiClient.getUserActivityReport(userId, startDate, endDate);
      setReports(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch user activity report';
      setReportsError(message);
      console.error('Error fetching user activity report:', error);
    } finally {
      setReportsLoading(false);
    }
  }, []);

  // ============================================================================
  // Initial Load
  // ============================================================================

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  return {
    // Family Members
    members,
    membersLoading,
    membersError,
    fetchMembers,
    createMember,
    updateMember,
    deleteMember,

    // Parental Controls
    controls,
    controlsLoading,
    controlsError,
    fetchControls,
    updateControls,

    // Activity Reports
    reports,
    reportsLoading,
    reportsError,
    fetchReports,
    fetchUserReport,
  };
}
