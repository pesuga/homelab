/**
 * Custom hook for Phase 2 system status and monitoring
 * Focuses on what's working: Phase 2 health, stats, and prompt system
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Phase2Health, SystemStats } from '@/lib/api-client';

export interface SystemLayer {
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency_ms?: number;
  details?: any;
  last_check: string;
}

export interface UseMemoryDataReturn {
  // System status
  systemHealth: Phase2Health | null;
  systemStats: SystemStats | null;
  layers: SystemLayer[];
  loading: boolean;
  error: string | null;

  // Operations
  fetchSystemHealth: () => Promise<void>;
  fetchSystemStats: () => Promise<void>;
  refreshSystem: () => Promise<void>;

  // Search state
  searchQuery: string;
  setSearchQuery: (query: string) => void;
}

export function useMemoryData(): UseMemoryDataReturn {
  const [systemHealth, setSystemHealth] = useState<Phase2Health | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [layers, setLayers] = useState<SystemLayer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch system health
  const fetchSystemHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const health = await apiClient.getPhase2Health();
      setSystemHealth(health);

      // Transform health data into layers
      const systemLayers: SystemLayer[] = [
        {
          name: 'Redis',
          status: health.layers.redis?.status === 'healthy' ? 'healthy' : 'unhealthy',
          latency_ms: health.layers.redis?.latency_ms,
          details: health.layers.redis,
          last_check: health.timestamp
        },
        {
          name: 'Mem0',
          status: health.layers.mem0?.status === 'healthy' ? 'healthy' : 'unhealthy',
          latency_ms: health.layers.mem0?.latency_ms,
          details: health.layers.mem0,
          last_check: health.timestamp
        },
        {
          name: 'Qdrant',
          status: health.layers.qdrant?.status === 'healthy' ? 'healthy' : 'unhealthy',
          latency_ms: health.layers.qdrant?.latency_ms,
          details: {
            ...health.layers.qdrant,
            collections: health.layers.qdrant?.collections
          },
          last_check: health.timestamp
        }
      ];
      setLayers(systemLayers);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch system health';
      setError(message);
      console.error('Error fetching system health:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch system statistics
  const fetchSystemStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const stats = await apiClient.getSystemStats();
      setSystemStats(stats);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch system statistics';
      setError(message);
      console.error('Error fetching system statistics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Refresh all system data
  const refreshSystem = useCallback(async () => {
    await Promise.all([
      fetchSystemHealth(),
      fetchSystemStats()
    ]);
  }, [fetchSystemHealth, fetchSystemStats]);

  // Auto-fetch on mount
  useEffect(() => {
    refreshSystem();
  }, [refreshSystem]);

  return {
    systemHealth,
    systemStats,
    layers,
    loading,
    error,
    fetchSystemHealth,
    fetchSystemStats,
    refreshSystem,
    searchQuery,
    setSearchQuery,
  };
}