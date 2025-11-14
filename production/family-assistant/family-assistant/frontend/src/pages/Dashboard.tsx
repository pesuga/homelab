import React from 'react';
import { useSystemHealth } from '@/contexts/SystemHealthContext';
import { MetricCard } from '@/components/MetricCard';
import { SystemStatusChart } from '@/components/SystemStatusChart';
import { RecentConversations } from '@/components/RecentConversations';
import { ServiceGrid } from '@/components/ServiceGrid';
import { ActivityFeed } from '@/components/ActivityFeed';
import {
  Activity,
  Users,
  MessageSquare,
  HardDrive,
  Cpu,
  Wifi,
  Database,
  Zap,
  Clock,
  TrendingUp,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { systemHealth, isLoading, isRefreshing, error } = useSystemHealth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-ctp-blue mx-auto"></div>
          <p className="mt-4 text-ctp-subtext1">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-ctp-red">Error loading dashboard: {error}</p>
        </div>
      </div>
    );
  }

  if (!systemHealth) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-ctp-subtext1">No system health data available</p>
        </div>
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatUptime = (timestamp: string) => {
    const uptime = Date.now() - new Date(timestamp).getTime();
    const hours = Math.floor(uptime / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ctp-text">Dashboard</h1>
          <p className="text-ctp-subtext1">Real-time homelab monitoring and insights</p>
        </div>
        <div className="flex items-center gap-2">
          {isRefreshing && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-ctp-blue"></div>
          )}
          <div className="text-sm text-ctp-subtext0">
            Last updated: {new Date(systemHealth.timestamp).toLocaleString()}
          </div>
        </div>
      </div>

      {/* System Status Banner */}
      <div className={`p-4 rounded-lg border ${
        systemHealth.status === 'healthy'
          ? 'bg-ctp-green/10 border-ctp-green text-ctp-green'
          : systemHealth.status === 'warning'
          ? 'bg-ctp-yellow/10 border-ctp-yellow text-ctp-yellow'
          : 'bg-ctp-red/10 border-ctp-red text-ctp-red'
      }`}>
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          <span className="font-medium">
            System Status: {systemHealth.status.charAt(0).toUpperCase() + systemHealth.status.slice(1)}
          </span>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="CPU Usage"
          value={`${systemHealth.system.cpu.usage.toFixed(1)}%`}
          icon={Cpu}
          trend={systemHealth.system.cpu.usage > 70 ? 'up' : 'stable'}
          color="blue"
        />
        <MetricCard
          title="Memory"
          value={`${systemHealth.system.memory.percentage.toFixed(1)}%`}
          subtitle={`${formatBytes(systemHealth.system.memory.used)} / ${formatBytes(systemHealth.system.memory.total)}`}
          icon={Zap}
          trend={systemHealth.system.memory.percentage > 80 ? 'up' : 'stable'}
          color="purple"
        />
        <MetricCard
          title="Disk Usage"
          value={`${systemHealth.system.disk.percentage.toFixed(1)}%`}
          subtitle={`${formatBytes(systemHealth.system.disk.used)} / ${formatBytes(systemHealth.system.disk.total)}`}
          icon={HardDrive}
          trend={systemHealth.system.disk.percentage > 85 ? 'up' : 'stable'}
          color="green"
        />
        <MetricCard
          title="Network"
          value={`${(-systemHealth.system.network.download / 1024 / 1024).toFixed(1)} MB/s`}
          subtitle={`${(systemHealth.system.network.upload / 1024 / 1024).toFixed(1)} MB/s up`}
          icon={Wifi}
          trend="stable"
          color="cyan"
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Status Chart */}
        <div className="metric-card">
          <h2 className="text-lg font-semibold text-ctp-text mb-4">System Performance</h2>
          <SystemStatusChart data={systemHealth.system} />
        </div>

        {/* Activity Feed */}
        <div className="metric-card">
          <h2 className="text-lg font-semibold text-ctp-text mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Recent Activity
          </h2>
          <ActivityFeed />
        </div>
      </div>

      {/* Services and Conversations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Grid */}
        <div className="metric-card">
          <h2 className="text-lg font-semibold text-ctp-text mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Services
          </h2>
          <ServiceGrid services={systemHealth.services} />
        </div>

        {/* Recent Conversations */}
        <div className="metric-card">
          <h2 className="text-lg font-semibold text-ctp-text mb-4 flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Recent Conversations
          </h2>
          <RecentConversations />
        </div>
      </div>
    </div>
  );
};