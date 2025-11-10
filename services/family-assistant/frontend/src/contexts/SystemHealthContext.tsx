import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { SystemHealth, SystemMetrics, ServiceStatus } from '@/types';

interface SystemHealthContextType {
  systemHealth: SystemHealth | null;
  isLoading: boolean;
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
  const [error, setError] = useState<string | null>(null);

  const fetchSystemHealth = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch system health from the API
      const healthResponse = await fetch('/api/health');
      const healthData = await healthResponse.json();

      // Fetch detailed system metrics
      const metricsResponse = await fetch('/api/system/metrics');
      const metricsData = await metricsResponse.json();

      // Fetch service statuses
      const servicesResponse = await fetch('/api/system/services');
      const servicesData = await servicesResponse.json();

      setSystemHealth({
        status: determineOverallStatus(healthData, servicesData),
        timestamp: new Date().toISOString(),
        services: servicesData,
        system: metricsData,
      });
    } catch (err) {
      console.error('Error fetching system health:', err);
      setError('Failed to fetch system health data');
    } finally {
      setIsLoading(false);
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
    fetchSystemHealth();

    const interval = setInterval(fetchSystemHealth, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const value: SystemHealthContextType = {
    systemHealth,
    isLoading,
    error,
    refreshHealth: fetchSystemHealth,
  };

  return (
    <SystemHealthContext.Provider value={value}>
      {children}
    </SystemHealthContext.Provider>
  );
};