export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  timestamp: string;
  services: ServiceStatus[];
  system: SystemMetrics;
}

export interface ServiceStatus {
  name: string;
  status: 'running' | 'stopped' | 'error' | 'warning';
  url?: string;
  responseTime?: number;
  lastCheck: string;
  details?: Record<string, any>;
}

export interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    upload: number;
    download: number;
  };
  gpu?: {
    usage: number;
    temperature: number;
    memory: {
      used: number;
      total: number;
    };
  };
}

export interface ArchitectureInfo {
  name: string;
  version: string;
  description: string;
  components: ArchitectureComponent[];
  lastUpdated: string;
}

export interface ArchitectureComponent {
  name: string;
  type: 'service' | 'database' | 'queue' | 'storage' | 'network' | 'ai';
  status: 'active' | 'inactive' | 'degraded';
  description: string;
  details?: Record<string, any>;
  connections?: string[];
}

export interface FamilyMember {
  id: string;
  name: string;
  role: 'parent' | 'teenager' | 'child';
  avatar?: string;
  status: 'online' | 'offline';
  lastSeen: string;
  permissions: string[];
}

export interface ConversationSummary {
  id: string;
  familyMember: string;
  lastMessage: string;
  timestamp: string;
  messageCount: number;
  hasMedia: boolean;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  service?: string;
}

export interface DashboardStats {
  totalConversations: number;
  activeUsers: number;
  mediaProcessed: number;
  systemUptime: string;
  responseTime: number;
}

export interface WebSocketMessage {
  type: 'health_update' | 'alert' | 'metric_update' | 'conversation_update';
  data: any;
  timestamp: string;
}