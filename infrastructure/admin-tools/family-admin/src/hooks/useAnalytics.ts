/**
 * Custom hook for managing sub-agent analytics data
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { AnalyticsOverview, ExecutionTrace } from '@/types/analytics';

interface UseAnalyticsReturn {
  overview: AnalyticsOverview | null;
  traceData: ExecutionTrace | null;
  loading: boolean;
  error: string | null;
  fetchTrace: (executionId: string) => Promise<void>;
  refreshOverview: () => Promise<void>;
}

export function useAnalytics(): UseAnalyticsReturn {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [traceData, setTraceData] = useState<ExecutionTrace | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch overview data
  const refreshOverview = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getAnalyticsOverview();
      setOverview(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch analytics overview';
      setError(message);
      console.error('Error fetching analytics overview:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch execution trace detail
  const fetchTrace = useCallback(async (executionId: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getExecutionTrace(executionId);
      setTraceData(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch execution trace';
      setError(message);
      console.error('Error fetching execution trace:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    refreshOverview();
  }, [refreshOverview]);

  return {
    overview,
    traceData,
    loading,
    error,
    fetchTrace,
    refreshOverview,
  };
}
