/**
 * Custom hook for managing dashboard data including Phase 2 health and statistics
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Phase2Health, SystemStats } from '@/lib/api-client';

interface UseDashboardDataReturn {
  health: Phase2Health | null;
  stats: SystemStats | null;
  loading: boolean;
  error: string | null;

  // Operations
  refreshHealth: () => Promise<void>;
  refreshStats: () => Promise<void>;
  refreshAll: () => Promise<void>;
}

export function useDashboardData(): UseDashboardDataReturn {
  const [health, setHealth] = useState<Phase2Health | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch Phase 2 health data
  const refreshHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getPhase2Health();
      setHealth(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch health data';
      setError(message);
      console.error('Error fetching health data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch system statistics
  const refreshStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getSystemStats();
      setStats(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch system stats';
      setError(message);
      console.error('Error fetching system stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh all dashboard data
  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [healthData, statsData] = await Promise.all([
        apiClient.getPhase2Health(),
        apiClient.getSystemStats(),
      ]);

      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch dashboard data';
      setError(message);
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  return {
    health,
    stats,
    loading,
    error,
    refreshHealth,
    refreshStats,
    refreshAll,
  };
}
