/**
 * Custom hook for managing sub-agent and chat analytics data
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { AnalyticsOverview, ExecutionTrace, ChatOverviewMetrics, ChatLogEntry, TokenStats } from '@/types/analytics';

interface UseAnalyticsReturn {
  // Sub-agent analytics
  overview: AnalyticsOverview | null;
  traceData: ExecutionTrace | null;
  // Chat analytics
  chatOverview: ChatOverviewMetrics | null;
  chatLogs: ChatLogEntry[] | null;
  tokenStats: TokenStats | null;
  // State
  loading: boolean;
  error: string | null;
  // Actions
  fetchTrace: (executionId: string) => Promise<void>;
  refreshOverview: () => Promise<void>;
  refreshChatAnalytics: (timeRange?: string) => Promise<void>;
  refreshChatLogs: (limit?: number, timeRange?: string) => Promise<void>;
  refreshTokenStats: (timeRange?: string) => Promise<void>;
}

export function useAnalytics(): UseAnalyticsReturn {
  // Sub-agent analytics state
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [traceData, setTraceData] = useState<ExecutionTrace | null>(null);

  // Chat analytics state
  const [chatOverview, setChatOverview] = useState<ChatOverviewMetrics | null>(null);
  const [chatLogs, setChatLogs] = useState<ChatLogEntry[] | null>(null);
  const [tokenStats, setTokenStats] = useState<TokenStats | null>(null);

  // Shared state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch sub-agent overview data
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

  // Fetch chat analytics overview
  const refreshChatAnalytics = useCallback(async (timeRange: string = '24h') => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getChatAnalyticsOverview(timeRange);
      setChatOverview(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch chat analytics';
      setError(message);
      console.error('Error fetching chat analytics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch chat logs
  const refreshChatLogs = useCallback(async (limit: number = 50, timeRange: string = '24h') => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getChatLogs(limit, timeRange);
      setChatLogs(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch chat logs';
      setError(message);
      console.error('Error fetching chat logs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch token statistics
  const refreshTokenStats = useCallback(async (timeRange: string = '7d') => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getChatTokenStats(timeRange);
      setTokenStats(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch token stats';
      setError(message);
      console.error('Error fetching token stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial data load
  useEffect(() => {
    refreshOverview();
    refreshChatAnalytics();
  }, [refreshOverview, refreshChatAnalytics]);

  return {
    overview,
    traceData,
    chatOverview,
    chatLogs,
    tokenStats,
    loading,
    error,
    fetchTrace,
    refreshOverview,
    refreshChatAnalytics,
    refreshChatLogs,
    refreshTokenStats,
  };
}
