/**
 * Dashboard Component
 *
 * Main dashboard with system overview and metrics
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { authClient } from '../auth/authClient';

interface SystemHealth {
  status: string;
  ollama: string;
  mem0: string;
  postgres: string;
  redis: string;
  qdrant: string;
  overall: 'healthy' | 'warning' | 'critical';
  alerts: Array<{
    service: string;
    level: 'warning' | 'error';
    message: string;
  }>;
}

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    total: number;
    used: number;
    percentage: number;
  };
  disk: {
    total: number;
    used: number;
    percentage: number;
  };
  uptime: number;
  network: {
    bytes_sent: number;
    bytes_received: number;
  };
}

interface DashboardStats {
  users: number;
  conversations: number;
  messages: number;
  recent_activity_24h: number;
  system: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    uptime_hours: number;
  };
}

interface Metric {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
}

const Dashboard: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      // Dashboard endpoints don't require authentication
      // Use direct fetch to avoid authClient's /api/v1 prefix
      const baseUrl = window.location.origin;

      const healthResponse = await fetch(`${baseUrl}/api/dashboard/system-health`);
      if (healthResponse.ok) {
        const health = await healthResponse.json();
        setSystemHealth(health);
      }

      const metricsResponse = await fetch(`${baseUrl}/api/dashboard/metrics`);
      if (metricsResponse.ok) {
        const metrics = await metricsResponse.json();
        setSystemMetrics(metrics);
      }

      const statsResponse = await fetch(`${baseUrl}/api/dashboard/stats`);
      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setDashboardStats(stats);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getRealMetrics = (): Metric[] => {
    if (!dashboardStats || !systemMetrics) {
      return [
        { label: 'Family Members', value: 'Loading...', trend: 'neutral' },
        { label: 'Conversations Today', value: 'Loading...', trend: 'neutral' },
        { label: 'AI Response Time', value: 'Loading...', trend: 'neutral' },
        { label: 'Storage Used', value: 'Loading...', trend: 'neutral' },
      ];
    }

    return [
      {
        label: 'Family Members',
        value: dashboardStats?.users || 0,
        change: dashboardStats?.users > 0 ? 'Active users' : 'No users yet',
        trend: dashboardStats?.users > 0 ? 'up' : 'neutral'
      },
      {
        label: 'Total Conversations',
        value: dashboardStats?.conversations || 0,
        change: dashboardStats?.conversations > 0 ? 'Total activity' : 'No conversations',
        trend: dashboardStats?.conversations > 5 ? 'up' : 'neutral'
      },
      {
        label: 'Messages',
        value: dashboardStats?.messages || 0,
        change: dashboardStats?.messages > 0 ? 'AI responses' : 'No messages',
        trend: dashboardStats?.messages > 10 ? 'up' : 'neutral'
      },
      {
        label: 'CPU Usage',
        value: systemMetrics ? `${systemMetrics.cpu.usage.toFixed(1)}%` : 'Loading...',
        change: systemMetrics && systemMetrics.cpu.usage > 80 ? 'High usage' : 'Normal',
        trend: systemMetrics && systemMetrics.cpu.usage > 80 ? 'down' : 'up'
      },
    ];
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return '📈';
      case 'down':
        return '📉';
      default:
        return '➡️';
    }
  };

  const getTrendColor = (trend?: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Welcome back, {user?.first_name || user?.username}!</p>
        </div>
        <button
          onClick={refreshUser}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
        {isLoading ? (
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        ) : systemHealth ? (
          <div>
            {/* Overall Status */}
            <div className="flex items-center space-x-3 mb-4">
              <div className={`w-4 h-4 rounded-full ${
                systemHealth.overall === 'healthy' ? 'bg-green-500' :
                systemHealth.overall === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
              }`}></div>
              <div>
                <p className="text-sm font-medium text-gray-900">Overall System Status</p>
                <p className="text-sm text-gray-600 capitalize">{systemHealth.overall}</p>
              </div>
            </div>

            {/* Individual Services */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">API Status</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.status}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.ollama === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Ollama LLM</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.ollama}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.postgres === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">PostgreSQL</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.postgres}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.redis === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Redis</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.redis}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.qdrant === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Qdrant</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.qdrant}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  systemHealth.mem0 === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Mem0</p>
                  <p className="text-sm text-gray-600 capitalize">{systemHealth.mem0}</p>
                </div>
              </div>
            </div>

            {/* Alerts */}
            {systemHealth.alerts && systemHealth.alerts.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-900 mb-2">System Alerts</h3>
                <div className="space-y-2">
                  {systemHealth.alerts.map((alert, index) => (
                    <div key={index} className={`p-3 rounded-lg border ${
                      alert.level === 'error'
                        ? 'bg-red-50 border-red-200 text-red-700'
                        : 'bg-yellow-50 border-yellow-200 text-yellow-700'
                    }`}>
                      <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          alert.level === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                        }`}></div>
                        <div>
                          <p className="text-sm font-medium">{alert.service}</p>
                          <p className="text-sm">{alert.message}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500">Unable to load system health</p>
        )}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {getRealMetrics().map((metric, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{metric.label}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
              </div>
              <div className="text-2xl">
                {getTrendIcon(metric.trend)}
              </div>
            </div>
            {metric.change && (
              <p className={`text-sm mt-2 ${getTrendColor(metric.trend)}`}>
                {metric.change}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        {dashboardStats ? (
          <div className="space-y-4">
            {dashboardStats.users > 0 && (
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Registered Users</p>
                  <p className="text-sm text-gray-600">{dashboardStats.users} users in the system</p>
                </div>
              </div>
            )}
            {dashboardStats.conversations > 0 && (
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Total Conversations</p>
                  <p className="text-sm text-gray-600">{dashboardStats.conversations} conversations recorded</p>
                </div>
              </div>
            )}
            {dashboardStats.messages > 0 && (
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Messages Exchanged</p>
                  <p className="text-sm text-gray-600">{dashboardStats.messages} messages sent</p>
                </div>
              </div>
            )}
            {dashboardStats.recent_activity_24h > 0 && (
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Recent Activity</p>
                  <p className="text-sm text-gray-600">{dashboardStats.recent_activity_24h} activities in last 24h</p>
                </div>
              </div>
            )}
            {dashboardStats.conversations === 0 && (
              <p className="text-gray-500 text-sm">No conversations yet. Start the first chat!</p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => window.location.href = '/chat'}
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="font-medium text-gray-900">Start Conversation</h3>
            </div>
            <p className="text-sm text-gray-600">Chat with the AI assistant</p>
          </button>
          <button
            onClick={() => window.location.href = '/memory'}
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="font-medium text-gray-900">Browse Memories</h3>
            </div>
            <p className="text-sm text-gray-600">View saved memories and knowledge</p>
          </button>
          <button
            onClick={() => window.location.href = '/analytics'}
            className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
          >
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="font-medium text-gray-900">View Analytics</h3>
            </div>
            <p className="text-sm text-gray-600">Usage statistics and insights</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;