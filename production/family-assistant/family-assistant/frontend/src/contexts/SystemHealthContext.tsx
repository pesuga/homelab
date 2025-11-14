import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { SystemHealth, SystemMetrics, ServiceStatus } from '@/types';
import { apiFetch, API_ENDPOINTS } from '@/utils/api';

interface SystemHealthContextType {
  systemHealth: SystemHealth | null;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  refreshHealth: () => Promise<void>;
}

const SystemHealthContext = createContext<SystemHealthContextType | undefined>(undefined);

export const useSystemHealth = () => {
  const context = useContext(SystemHealthContext);
  if (context === undefined) {
    throw new Error('useSystemHealth must be used within a SystemHealthProvider');
  }
  return context;
};

interface SystemHealthProviderProps {
  children: ReactNode;
}

export const SystemHealthProvider: React.FC<SystemHealthProviderProps> = ({ children }) => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSystemHealth = async (isBackgroundRefresh = false) => {
    try {
      // Only show loading spinner on initial load, not on background refreshes
      if (!isBackgroundRefresh && !systemHealth) {
        setIsLoading(true);
      } else if (isBackgroundRefresh) {
        setIsRefreshing(true);
      }
      setError(null);

      // Fetch system health from the unified dashboard endpoint
      const dashboardResponse = await apiFetch(API_ENDPOINTS.dashboardHealth);
      const dashboardData = await dashboardResponse.json();

      // Dashboard endpoint returns all data in one response
      setSystemHealth({
        status: dashboardData.status || 'healthy',
        timestamp: dashboardData.timestamp || new Date().toISOString(),
        services: dashboardData.services || [],
        system: dashboardData.system || {},
      });
    } catch (err) {
      console.error('Error fetching system health:', err);
      // Only set error if we don't have cached data
      if (!systemHealth) {
        setError('Failed to fetch system health data');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const determineOverallStatus = (health: any, services: ServiceStatus[]): 'healthy' | 'warning' | 'error' => {
    // Check if any critical services are down
    const criticalServicesDown = services.filter(s =>
      ['Family Assistant', 'PostgreSQL', 'Redis', 'Ollama'].includes(s.name) && s.status === 'error'
    ).length;

    if (criticalServicesDown > 0) return 'error';

    // Check if any services have warnings
    const warningServices = services.filter(s => s.status === 'warning').length;
    if (warningServices > 0) return 'warning';

    // Check system metrics for warnings
    if (health.system?.cpu?.usage > 80 || health.system?.memory?.percentage > 85) {
      return 'warning';
    }

    return 'healthy';
  };

  // Set up interval for real-time updates
  useEffect(() => {
    // Initial load (show spinner)
    fetchSystemHealth(false);

    // Background refreshes (no spinner, keep showing old data)
    const interval = setInterval(() => fetchSystemHealth(true), 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const value: SystemHealthContextType = {
    systemHealth,
    isLoading,
    isRefreshing,
    error,
    refreshHealth: () => fetchSystemHealth(true),
  };

  return (
    <SystemHealthContext.Provider value={value}>
      {children}
    </SystemHealthContext.Provider>
  );
};