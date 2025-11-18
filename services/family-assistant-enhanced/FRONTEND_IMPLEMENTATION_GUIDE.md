# Family Assistant Frontend Implementation Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Authentication & Security](#authentication--security)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Component Structure](#component-structure)
5. [State Management](#state-management)
6. [MCP System Implementation](#mcp-system-implementation)
7. [Memory & Prompt Management](#memory--prompt-management)
8. [Family Management Features](#family-management-features)
9. [Dashboard & Analytics](#dashboard--analytics)
10. [UI Components & Design System](#ui-components--design-system)
11. [Real-time Features](#real-time-features)
12. [Error Handling & User Experience](#error-handling--user-experience)
13. [Testing Strategy](#testing-strategy)
14. [Deployment Considerations](#deployment-considerations)

---

## Architecture Overview

### System Architecture
The Family Assistant platform is built with a **React + TypeScript frontend** communicating with a **FastAPI Python backend**. The system is designed with privacy-first principles and runs entirely on-premises.

### Key Architectural Patterns
- **JWT Authentication**: Token-based auth with role-based access control (RBAC)
- **RESTful API**: Comprehensive REST API with OpenAPI/Swagger documentation
- **WebSocket Integration**: Real-time updates for dashboard and chat features
- **Multi-layer Memory System**: Redis, PostgreSQL, Qdrant vector database integration
- **MCP (Model Context Protocol)**: Extensible tool system for AI capabilities

### Frontend Tech Stack
```typescript
// Recommended Stack
- React 18+ with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Zustand for state management
- React Query for API calls
- React Router for navigation
- Axios for HTTP requests
- React Hook Form for forms
- Zod for validation
- React Hot Toast for notifications
```

---

## Authentication & Security

### JWT Authentication Flow

#### 1. Login Process
```typescript
// POST /api/v1/auth/login
interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: {
    id: string;
    email: string;
    role: "parent" | "grandparent" | "teenager" | "child" | "member";
    is_admin: boolean;
    display_name: string;
    first_name: string;
    last_name: string;
  };
}
```

#### 2. Token Management
```typescript
// Store tokens securely (httpOnly cookies recommended)
const authStore = create<AuthStore>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,

  login: async (credentials: LoginRequest) => {
    const response = await api.post('/auth/login', credentials);
    const { user, access_token, refresh_token } = response.data;

    set({
      user,
      accessToken: access_token,
      refreshToken: refresh_token
    });

    // Store in secure httpOnly cookie or localStorage
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
  },

  logout: () => {
    set({ user: null, accessToken: null, refreshToken: null });
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  refreshAccessToken: async () => {
    const refreshToken = get().refreshToken;
    if (!refreshToken) throw new Error('No refresh token');

    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    });

    const { access_token } = response.data;
    set({ accessToken: access_token });
    localStorage.setItem('access_token', access_token);
  }
}));
```

#### 3. API Client with Token Interceptor
```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: 10000,
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const authStore = useAuthStore.getState();
        await authStore.refreshAccessToken();

        const token = localStorage.getItem('access_token');
        originalRequest.headers.Authorization = `Bearer ${token}`;

        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        const authStore = useAuthStore.getState();
        authStore.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

### Role-Based Access Control (RBAC)

#### Role Definitions
```typescript
enum UserRole {
  PARENT = 'parent',
  GRANDPARENT = 'grandparent',
  TEENAGER = 'teenager',
  CHILD = 'child',
  MEMBER = 'member'
}

interface RolePermissions {
  canManageFamily: boolean;
  canAccessDashboard: boolean;
  canUseMCPTools: boolean;
  canManageSettings: boolean;
  canViewAnalytics: boolean;
}

const ROLE_PERMISSIONS: Record<UserRole, RolePermissions> = {
  [UserRole.PARENT]: {
    canManageFamily: true,
    canAccessDashboard: true,
    canUseMCPTools: true,
    canManageSettings: true,
    canViewAnalytics: true
  },
  [UserRole.GRANDPARENT]: {
    canManageFamily: false,
    canAccessDashboard: true,
    canUseMCPTools: true,
    canManageSettings: false,
    canViewAnalytics: true
  },
  [UserRole.TEENAGER]: {
    canManageFamily: false,
    canAccessDashboard: false,
    canUseMCPTools: true,
    canManageSettings: false,
    canViewAnalytics: false
  },
  [UserRole.CHILD]: {
    canManageFamily: false,
    canAccessDashboard: false,
    canUseMCPTools: false,
    canManageSettings: false,
    canViewAnalytics: false
  },
  [UserRole.MEMBER]: {
    canManageFamily: false,
    canAccessDashboard: false,
    canUseMCPTools: true,
    canManageSettings: false,
    canViewAnalytics: false
  }
};
```

#### Permission Guard Component
```typescript
// components/PermissionGuard.tsx
interface PermissionGuardProps {
  children: React.ReactNode;
  permission?: keyof RolePermissions;
  fallback?: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  permission,
  fallback = <div>Access Denied</div>
}) => {
  const { user } = useAuthStore();

  if (!user) return fallback;

  const permissions = ROLE_PERMISSIONS[user.role];

  if (permission && !permissions[permission]) {
    return fallback;
  }

  return <>{children}</>;
};
```

---

## API Endpoints Reference

### Base URL
```
Development: http://localhost:8001
Production: https://family-assistant.homelab.pesulabs.net
```

### Authentication Endpoints
```typescript
// Authentication
POST   /api/v1/auth/login                    // User login
POST   /api/v1/auth/login/json              // JSON login (alternative)
GET    /api/v1/auth/me                      // Get current user profile
POST   /api/v1/auth/verify                  // Verify token validity

// Token Management
POST   /api/v1/auth/refresh                 // Refresh access token
POST   /api/v1/auth/logout                  // Logout user
```

### Family Management Endpoints
```typescript
// Family Members
POST   /api/v1/family/members               // Create family member
GET    /api/v1/family/members               // List all family members
GET    /api/v1/family/members/{id}          // Get specific member
PATCH  /api/v1/family/members/{id}          // Update member
DELETE /api/v1/family/members/{id}          // Delete member

// Permissions
POST   /api/v1/family/permissions/check    // Check user permissions
POST   /api/v1/family/permissions/grant    // Grant permissions
DELETE /api/v1/family/permissions/{userId}/{permission} // Revoke permission
GET    /api/v1/family/permissions/{userId} // Get user permissions

// Parental Controls
POST   /api/v1/family/parental-controls     // Create parental controls
GET    /api/v1/family/parental-controls/{childId} // Get parental controls
PATCH  /api/v1/family/parental-controls/{childId} // Update parental controls
POST   /api/v1/family/screen-time            // Log screen time
GET    /api/v1/family/screen-time/{userId}/{date} // Get screen time logs

// Content Filtering
POST   /api/v1/family/content-filter/check   // Check content filter
GET    /api/v1/family/content-filter/logs/{userId} // Get filter logs
GET    /api/v1/family/content-filter/stats/{userId} // Get filter stats
POST   /api/v1/family/content-filter/keywords/{childId} // Add keywords
DELETE /api/v1/family/content-filter/keywords/{childId}/{keyword} // Remove keyword
POST   /api/v1/family/content-filter/domains/{childId}/blocked // Block domains
POST   /api/v1/family/content-filter/domains/{childId}/allowed  // Allow domains

// Audit Logs
GET    /api/v1/family/audit-logs             // Get audit logs
```

### MCP (Model Context Protocol) Endpoints
```typescript
// MCP Server Management (Admin only)
GET    /api/v1/mcp/servers                   // List MCP servers
POST   /api/v1/mcp/servers                   // Register new MCP server
POST   /api/v1/mcp/servers/{name}/start      // Start MCP server
POST   /api/v1/mcp/servers/{name}/stop       // Stop MCP server
DELETE /api/v1/mcp/servers/{name}           // Delete MCP server

// MCP Tools
GET    /api/v1/mcp/tools                     // List available tools (filtered by permissions)
GET    /api/v1/mcp/tools/{toolName}         // Get specific tool details
POST   /api/v1/mcp/tools/execute             // Execute MCP tool

// MCP Permissions (Admin only)
GET    /api/v1/mcp/permissions              // List all MCP permissions
POST   /api/v1/mcp/permissions              // Update MCP permission
DELETE /api/v1/mcp/permissions/{tool}/{server}/{role} // Delete permission

// MCP Analytics
GET    /api/v1/mcp/metrics                   // Get MCP usage metrics
GET    /api/v1/mcp/usage                     // Get usage history
GET    /api/v1/mcp/executions                // Get recent executions
GET    /api/v1/mcp/health                    // MCP health check

// Personal MCP (User-facing)
GET    /api/v1/personal-mcp/arcade/discover  // Discover Arcade.dev servers
POST   /api/v1/personal-mcp/arcade/connect   // Connect to Arcade.dev server
POST   /api/v1/personal-mcp/servers/local    // Add local MCP server
GET    /api/v1/personal-mcp/servers          // List personal MCP servers
DELETE /api/v1/personal-mcp/servers/{id}     // Remove personal MCP server
POST   /api/v1/personal-mcp/tools/execute    // Execute personal MCP tool

// Admin MCP (System configuration)
POST   /api/v1/admin-mcp/arcade/configure    // Configure Arcade.dev
POST   /api/v1/admin-mcp/arcade/sync          // Sync Arcade.dev
GET    /api/v1/admin-mcp/arcade/status        // Get Arcade.dev status
GET    /api/v1/admin-mcp/servers              // List system MCP servers
POST   /api/v1/admin-mcp/servers/custom       // Add custom MCP server
GET    /api/v1/admin-mcp/tools/available      // Get available tools
PUT    /api/v1/admin-mcp/tools/permissions    // Update tool permissions
GET    /api/v1/admin-mcp/analytics/usage      // Get usage analytics
GET    /api/v1/admin-mcp/analytics/by-role     // Get analytics by role
GET    /api/v1/admin-mcp/config/overview       // Get configuration overview
GET    /api/v1/admin-mcp/setup-guide           // Get setup guide
```

### Memory & Prompt Management (Phase 2)
```typescript
// Memory Management
POST   /api/phase2/memory/search             // Search memories
POST   /api/phase2/memory/save               // Save context to memory
GET    /api/phase2/memory/context/{convId}   // Get conversation context
POST   /api/phase2/memory/cleanup            // Cleanup old memories

// Prompt Management
POST   /api/phase2/prompts/build             // Build prompt from context
GET    /api/phase2/prompts/role/{role}       // Get role-specific prompts
GET    /api/phase2/prompts/core              // Get core system prompts

// User Profile
GET    /api/phase2/users/{userId}/profile    // Get user profile
PUT    /api/phase2/users/{userId}/profile    // Update user profile

// System Health & Stats
GET    /api/phase2/health                    // Memory system health
GET    /api/phase2/stats                     // Memory system statistics
GET    /api/phase2/test/prompt-assembly      // Test prompt assembly
```

### Family Tools (Member Interface)
```typescript
// Tool Management
GET    /api/v1/family-tools/tools            // List family tools
GET    /api/v1/family-tools/tools/categories  // Get tool categories
POST   /api/v1/family-tools/tools/execute    // Execute family tool
GET    /api/v1/family-tools/favorites        // Get favorite tools
POST   /api/v1/family-tools/favorites        // Add favorite tool
DELETE /api/v1/family-tools/favorites/{tool} // Remove favorite tool
GET    /api/v1/family-tools/recommendations  // Get tool recommendations
GET    /api/v1/family-tools/history           // Get tool usage history
GET    /api/v1/family-tools/stats             // Get tool usage stats
GET    /api/v1/family-tools/help              // Get tool help
GET    /api/v1/family-tools/quick-actions    // Get quick actions
```

### Enhanced Features (Phase 3)
```typescript
// Health & System
GET    /api/v3/health                        // Enhanced health check
GET    /api/v3/family-members                // List family members (enhanced)
POST   /api/v3/family-members                // Create family member (enhanced)
GET    /api/v3/family-members/{id}           // Get family member (enhanced)

// Home Assistant Integration
POST   /api/v3/home-assistant/automations    // Create automation
GET    /api/v3/home-assistant/automations    // List automations
POST   /api/v3/home-assistant/devices/{id}/control // Control device

// Matrix Integration
POST   /api/v3/matrix/rooms                 // Create Matrix room
POST   /api/v3/matrix/rooms/{id}/invite      // Invite to Matrix room

// Voice Services
POST   /api/v3/voice/speech-to-text          // Speech to text
POST   /api/v3/voice/text-to-speech          // Text to speech

// Dashboard
GET    /api/v3/dashboard/widgets             // Get dashboard widgets
GET    /api/v3/dashboard/analytics           // Get analytics data

// Conversations
POST   /api/v3/conversations/{id}/voice-interaction // Voice interaction

// System Configuration
GET    /api/v3/system/bilingual-setup       // Get bilingual setup
POST   /api/v3/system/parental-controls/{id} // Configure parental controls
GET    /api/v3/system/migration-status       // Get migration status
```

### WebSocket Endpoints
```typescript
// Real-time connections
WS     /ws/dashboard                         // Real-time dashboard updates
WS     /ws/chat/{conversationId}           // Real-time chat
WS     /ws/mcp/status                        // MCP server status updates
```

---

## Component Structure

### Recommended Folder Structure
```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI components
│   ├── forms/           # Form components
│   ├── layout/          # Layout components
│   └── features/        # Feature-specific components
├── pages/               # Route pages
│   ├── auth/           # Authentication pages
│   ├── dashboard/      # Dashboard pages
│   ├── family/         # Family management
│   ├── mcp/            # MCP system
│   ├── memory/         # Memory management
│   └── settings/       # Settings pages
├── hooks/               # Custom React hooks
├── lib/                 # Utilities and configuration
│   ├── api.ts          # API client
│   ├── auth.ts         # Auth utilities
│   ├── utils.ts        # General utilities
│   └── validations.ts  # Zod schemas
├── store/               # State management
├── types/               # TypeScript type definitions
└── styles/              # Global styles and themes
```

### Core Components

#### 1. Layout Components
```typescript
// components/layout/AppLayout.tsx
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { PermissionGuard } from '../PermissionGuard';

export const AppLayout: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <PermissionGuard>
            <Outlet />
          </PermissionGuard>
        </main>
      </div>
    </div>
  );
};
```

#### 2. Navigation Sidebar
```typescript
// components/layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { PermissionGuard } from '../PermissionGuard';
import { ROLE_PERMISSIONS } from '../../lib/auth';

interface NavItem {
  path: string;
  label: string;
  icon: React.ComponentType;
  permission?: keyof RolePermissions;
}

const navItems: NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: HomeIcon, permission: 'canAccessDashboard' },
  { path: '/family', label: 'Family', icon: UsersIcon, permission: 'canManageFamily' },
  { path: '/mcp', label: 'MCP Tools', icon: CpuIcon, permission: 'canUseMCPTools' },
  { path: '/memory', label: 'Memory', icon: BrainIcon },
  { path: '/chat', label: 'Chat', icon: MessageSquareIcon },
  { path: '/settings', label: 'Settings', icon: SettingsIcon, permission: 'canManageSettings' },
];

export const Sidebar: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="w-64 bg-white shadow-lg">
      <div className="p-4">
        <h1 className="text-xl font-bold text-gray-800">Family Assistant</h1>
      </div>

      <nav className="mt-4">
        {navItems.map((item) => (
          <PermissionGuard key={item.path} permission={item.permission} fallback={null}>
            <NavLink
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-2 text-sm font-medium rounded-md ${
                  isActive
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.label}
            </NavLink>
          </PermissionGuard>
        ))}
      </nav>

      <div className="absolute bottom-0 w-64 p-4 border-t">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
            {user?.first_name?.[0]?.toUpperCase()}
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">{user?.display_name}</p>
            <p className="text-xs text-gray-500">{user?.role}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
```

#### 3. Loading and Error States
```typescript
// components/ui/LoadingState.tsx
export const LoadingState: React.FC<{ message?: string }> = ({ message = "Loading..." }) => (
  <div className="flex items-center justify-center py-12">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span className="ml-2 text-gray-600">{message}</span>
  </div>
);

// components/ui/ErrorState.tsx
interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "Please try again later",
  onRetry
}) => (
  <div className="text-center py-12">
    <div className="text-red-500 mb-4">
      <ExclamationTriangleIcon className="w-12 h-12 mx-auto" />
    </div>
    <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 mb-4">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Try Again
      </button>
    )}
  </div>
);
```

---

## State Management

### Zustand Store Structure
```typescript
// store/auth.ts
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;

  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isLoading: false,

  login: async (credentials) => {
    set({ isLoading: true });
    try {
      const response = await api.post('/auth/login', credentials);
      const { user, access_token, refresh_token } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      set({ user, accessToken: access_token, refreshToken: refresh_token });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, accessToken: null, refreshToken: null });
  },

  refreshAccessToken: async () => {
    const refreshToken = get().refreshToken;
    if (!refreshToken) throw new Error('No refresh token');

    const response = await api.post('/auth/refresh', { refresh_token });
    const { access_token } = response.data;

    localStorage.setItem('access_token', access_token);
    set({ accessToken: access_token });
  },

  updateUser: (updates) => {
    set((state) => ({
      user: state.user ? { ...state.user, ...updates } : null
    }));
  }
}));

// store/mcp.ts
interface MCPState {
  servers: MCPServer[];
  tools: MCPTool[];
  isExecuting: boolean;
  executionHistory: MCPExecution[];

  fetchServers: () => Promise<void>;
  fetchTools: () => Promise<void>;
  executeTool: (toolName: string, parameters: any) => Promise<MCPExecutionResult>;
  startServer: (serverName: string) => Promise<void>;
  stopServer: (serverName: string) => Promise<void>;
}

export const useMCPStore = create<MCPState>((set, get) => ({
  servers: [],
  tools: [],
  isExecuting: false,
  executionHistory: [],

  fetchServers: async () => {
    try {
      const response = await api.get('/mcp/servers');
      set({ servers: response.data });
    } catch (error) {
      console.error('Failed to fetch MCP servers:', error);
      throw error;
    }
  },

  fetchTools: async () => {
    try {
      const response = await api.get('/mcp/tools');
      set({ tools: response.data });
    } catch (error) {
      console.error('Failed to fetch MCP tools:', error);
      throw error;
    }
  },

  executeTool: async (toolName, parameters) => {
    set({ isExecuting: true });
    try {
      const response = await api.post('/mcp/tools/execute', {
        tool_name: toolName,
        parameters
      });

      const execution = {
        id: uuidv4(),
        toolName,
        parameters,
        result: response.data,
        timestamp: new Date(),
        status: 'completed'
      };

      set((state) => ({
        executionHistory: [execution, ...state.executionHistory.slice(0, 49)]
      }));

      return response.data;
    } catch (error) {
      const execution = {
        id: uuidv4(),
        toolName,
        parameters,
        error: error.message,
        timestamp: new Date(),
        status: 'failed'
      };

      set((state) => ({
        executionHistory: [execution, ...state.executionHistory.slice(0, 49)]
      }));

      throw error;
    } finally {
      set({ isExecuting: false });
    }
  }
}));

// store/memory.ts
interface MemoryState {
  searchResults: MemorySearchResult[];
  isSearching: boolean;
  userContext: UserContext | null;

  searchMemories: (query: string) => Promise<void>;
  saveContext: (context: SaveContextRequest) => Promise<void>;
  getUserContext: (conversationId: string) => Promise<void>;
  buildPrompt: (context: PromptBuildRequest) => Promise<PromptBuildResponse>;
}

export const useMemoryStore = create<MemoryState>((set, get) => ({
  searchResults: [],
  isSearching: false,
  userContext: null,

  searchMemories: async (query) => {
    set({ isSearching: true });
    try {
      const response = await api.post('/phase2/memory/search', { query });
      set({ searchResults: response.data.results });
    } catch (error) {
      console.error('Failed to search memories:', error);
      throw error;
    } finally {
      set({ isSearching: false });
    }
  },

  saveContext: async (context) => {
    try {
      await api.post('/phase2/memory/save', context);
    } catch (error) {
      console.error('Failed to save context:', error);
      throw error;
    }
  }
}));
```

### React Query Integration
```typescript
// hooks/api/useFamilyMembers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';

export const useFamilyMembers = () => {
  return useQuery({
    queryKey: ['family-members'],
    queryFn: async () => {
      const response = await api.get('/family/members');
      return response.data;
    }
  });
};

export const useCreateFamilyMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (memberData: CreateMemberRequest) => {
      const response = await api.post('/family/members', memberData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['family-members'] });
      toast.success('Family member created successfully');
    },
    onError: (error) => {
      toast.error('Failed to create family member');
      console.error('Create family member error:', error);
    }
  });
};

export const useUpdateFamilyMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...updates }: UpdateMemberRequest) => {
      const response = await api.patch(`/family/members/${id}`, updates);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['family-members'] });
      queryClient.setQueryData(['family-member', variables.id], data);
      toast.success('Family member updated successfully');
    },
    onError: (error) => {
      toast.error('Failed to update family member');
      console.error('Update family member error:', error);
    }
  });
};
```

---

## MCP System Implementation

### MCP Management Interface

#### 1. MCP Server Management Component
```typescript
// pages/mcp/ServerManagement.tsx
import React, { useEffect } from 'react';
import { useMCPStore } from '../../store/mcp';
import { LoadingState } from '../../components/ui/LoadingState';
import { Button } from '../../components/ui/Button';

export const ServerManagement: React.FC = () => {
  const { servers, fetchServers, startServer, stopServer } = useMCPStore();

  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  const handleToggleServer = async (serverName: string, isRunning: boolean) => {
    try {
      if (isRunning) {
        await stopServer(serverName);
      } else {
        await startServer(serverName);
      }
      await fetchServers(); // Refresh servers list
    } catch (error) {
      console.error('Failed to toggle server:', error);
    }
  };

  if (!servers.length) {
    return <LoadingState message="Loading MCP servers..." />;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">MCP Servers</h1>
        <Button onClick={() => window.open('/mcp/servers/new', '_blank')}>
          Add Server
        </Button>
      </div>

      <div className="grid gap-4">
        {servers.map((server) => (
          <div key={server.name} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">{server.name}</h3>
                <p className="text-sm text-gray-500">{server.command}</p>
                <div className="flex items-center mt-2 space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    server.status === 'ONLINE'
                      ? 'bg-green-100 text-green-800'
                      : server.status === 'OFFLINE'
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {server.status}
                  </span>
                  <span className="text-sm text-gray-500">
                    {server.tools?.length || 0} tools
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Button
                  variant={server.status === 'ONLINE' ? 'danger' : 'primary'}
                  size="sm"
                  onClick={() => handleToggleServer(server.name, server.status === 'ONLINE')}
                  disabled={server.status === 'STARTING' || server.status === 'STOPPING'}
                >
                  {server.status === 'ONLINE' ? 'Stop' : 'Start'}
                </Button>
                <Button variant="secondary" size="sm">
                  Configure
                </Button>
              </div>
            </div>

            {server.error_message && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{server.error_message}</p>
              </div>
            )}

            {server.tools && server.tools.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Available Tools:</h4>
                <div className="flex flex-wrap gap-2">
                  {server.tools.map((tool) => (
                    <span
                      key={tool.name}
                      className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                    >
                      {tool.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 2. MCP Tool Execution Interface
```typescript
// pages/mcp/ToolExecution.tsx
import React, { useState } from 'react';
import { useMCPStore } from '../../store/mcp';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';

interface ToolExecutionForm {
  toolName: string;
  parameters: Record<string, any>;
}

export const ToolExecution: React.FC = () => {
  const { tools, executeTool, isExecuting, executionHistory } = useMCPStore();
  const [selectedTool, setSelectedTool] = useState<string>('');
  const [parameters, setParameters] = useState<Record<string, any>>({});

  const handleExecuteTool = async () => {
    if (!selectedTool) return;

    try {
      await executeTool(selectedTool, parameters);
      setParameters({});
      setSelectedTool('');
    } catch (error) {
      console.error('Tool execution failed:', error);
    }
  };

  const handleParameterChange = (key: string, value: any) => {
    setParameters(prev => ({ ...prev, [key]: value }));
  };

  const renderParameterInput = (tool: MCPTool) => {
    if (!tool.inputSchema || !tool.inputSchema.properties) return null;

    return Object.entries(tool.inputSchema.properties).map(([key, schema]: [string, any]) => (
      <div key={key} className="space-y-1">
        <label className="block text-sm font-medium text-gray-700">
          {key}
          {schema.required?.includes(key) && <span className="text-red-500">*</span>}
        </label>

        {schema.type === 'string' && schema.enum ? (
          <Select
            value={parameters[key] || ''}
            onChange={(value) => handleParameterChange(key, value)}
            options={schema.enum.map((option: string) => ({
              value: option,
              label: option
            }))}
          />
        ) : schema.type === 'string' ? (
          <input
            type="text"
            value={parameters[key] || ''}
            onChange={(e) => handleParameterChange(key, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={schema.description || `Enter ${key}`}
          />
        ) : schema.type === 'number' ? (
          <input
            type="number"
            value={parameters[key] || ''}
            onChange={(e) => handleParameterChange(key, Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={schema.description || `Enter ${key}`}
          />
        ) : schema.type === 'boolean' ? (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={parameters[key] || false}
              onChange={(e) => handleParameterChange(key, e.target.checked)}
              className="mr-2"
            />
            {schema.description || key}
          </label>
        ) : null}
      </div>
    ));
  };

  const selectedToolData = tools.find(tool => tool.name === selectedTool);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">MCP Tool Execution</h1>
        <p className="text-gray-600">Execute available MCP tools with custom parameters</p>
      </div>

      {/* Tool Selection */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Select Tool</h2>

        <Select
          value={selectedTool}
          onChange={setSelectedTool}
          options={tools.map(tool => ({
            value: tool.name,
            label: `${tool.name} - ${tool.description || 'No description'}`
          }))}
          placeholder="Choose a tool to execute"
        />
      </div>

      {/* Parameters */}
      {selectedToolData && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Parameters</h2>

          {selectedToolData.description && (
            <p className="text-sm text-gray-600 mb-4">{selectedToolData.description}</p>
          )}

          <div className="space-y-4">
            {renderParameterInput(selectedToolData)}
          </div>

          <div className="mt-6">
            <Button
              onClick={handleExecuteTool}
              disabled={isExecuting || !selectedTool}
              className="w-full"
            >
              {isExecuting ? 'Executing...' : 'Execute Tool'}
            </Button>
          </div>
        </div>
      )}

      {/* Execution History */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Execution History</h2>

        {executionHistory.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No tool executions yet</p>
        ) : (
          <div className="space-y-4">
            {executionHistory.map((execution) => (
              <div key={execution.id} className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">{execution.toolName}</h3>
                  <span className="text-sm text-gray-500">
                    {execution.timestamp.toLocaleString()}
                  </span>
                </div>

                {execution.status === 'completed' ? (
                  <div className="mt-2">
                    <p className="text-sm text-green-600">✅ Completed successfully</p>
                    {execution.result && (
                      <pre className="mt-2 p-2 bg-gray-50 text-xs rounded overflow-x-auto">
                        {JSON.stringify(execution.result, null, 2)}
                      </pre>
                    )}
                  </div>
                ) : (
                  <div className="mt-2">
                    <p className="text-sm text-red-600">❌ Execution failed</p>
                    {execution.error && (
                      <p className="text-sm text-red-500 mt-1">{execution.error}</p>
                    )}
                  </div>
                )}

                {execution.parameters && Object.keys(execution.parameters).length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">Parameters:</p>
                    <pre className="text-xs text-gray-600 mt-1">
                      {JSON.stringify(execution.parameters, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
```

#### 3. MCP Permissions Management (Admin)
```typescript
// pages/mcp/PermissionsManagement.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';

interface MCPPermission {
  tool_name: string;
  server_name: string;
  role: string;
  can_execute: boolean;
}

export const PermissionsManagement: React.FC = () => {
  const [permissions, setPermissions] = useState<MCPPermission[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      const response = await api.get('/mcp/permissions');
      setPermissions(response.data);
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const updatePermission = async (permission: MCPPermission) => {
    try {
      await api.post('/mcp/permissions', permission);
      await fetchPermissions();
    } catch (error) {
      console.error('Failed to update permission:', error);
    }
  };

  const deletePermission = async (toolName: string, serverName: string, role: string) => {
    try {
      await api.delete(`/mcp/permissions/${toolName}/${serverName}/${role}`);
      await fetchPermissions();
    } catch (error) {
      console.error('Failed to delete permission:', error);
    }
  };

  if (loading) {
    return <div>Loading permissions...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">MCP Permissions</h1>
        <p className="text-gray-600">Manage role-based access to MCP tools</p>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Current Permissions</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tool
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Server
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Can Execute
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {permissions.map((permission, index) => (
                <tr key={index}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {permission.tool_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {permission.server_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      permission.role === 'parent' ? 'bg-purple-100 text-purple-800' :
                      permission.role === 'grandparent' ? 'bg-blue-100 text-blue-800' :
                      permission.role === 'teenager' ? 'bg-green-100 text-green-800' :
                      permission.role === 'child' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {permission.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <input
                      type="checkbox"
                      checked={permission.can_execute}
                      onChange={(e) => updatePermission({
                        ...permission,
                        can_execute: e.target.checked
                      })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => deletePermission(
                        permission.tool_name,
                        permission.server_name,
                        permission.role
                      )}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Permission</h2>
        <PermissionForm onSubmit={updatePermission} />
      </div>
    </div>
  );
};

const PermissionForm: React.FC<{ onSubmit: (permission: MCPPermission) => void }> = ({ onSubmit }) => {
  const [formData, setFormData] = useState<Partial<MCPPermission>>({
    can_execute: true
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.tool_name && formData.server_name && formData.role) {
      onSubmit(formData as MCPPermission);
      setFormData({ can_execute: true });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Tool Name</label>
          <input
            type="text"
            value={formData.tool_name || ''}
            onChange={(e) => setFormData({ ...formData, tool_name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Server Name</label>
          <input
            type="text"
            value={formData.server_name || ''}
            onChange={(e) => setFormData({ ...formData, server_name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Role</label>
          <Select
            value={formData.role || ''}
            onChange={(value) => setFormData({ ...formData, role: value })}
            options={[
              { value: 'parent', label: 'Parent' },
              { value: 'grandparent', label: 'Grandparent' },
              { value: 'teenager', label: 'Teenager' },
              { value: 'child', label: 'Child' },
              { value: 'member', label: 'Member' }
            ]}
            required
          />
        </div>

        <div className="flex items-end">
          <Button type="submit" className="w-full">
            Add Permission
          </Button>
        </div>
      </div>
    </form>
  );
};
```

---

## Memory & Prompt Management

### Memory Search Interface
```typescript
// pages/memory/MemorySearch.tsx
import React, { useState } from 'react';
import { useMemoryStore } from '../../store/memory';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

export const MemorySearch: React.FC = () => {
  const { searchResults, isSearching, searchMemories } = useMemoryStore();
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearched(true);
    await searchMemories(query);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Memory Search</h1>
        <p className="text-gray-600">Search through family memories and context</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-4">
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories..."
          className="flex-1"
        />
        <Button type="submit" disabled={isSearching}>
          {isSearching ? 'Searching...' : 'Search'}
        </Button>
      </form>

      {searched && (
        <div className="space-y-4">
          {isSearching ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Searching memories...</p>
            </div>
          ) : searchResults.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No memories found for "{query}"</p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Found {searchResults.length} memories
              </p>
              {searchResults.map((result, index) => (
                <div key={index} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-medium text-gray-900">
                      {result.title || 'Untitled Memory'}
                    </h3>
                    <span className="text-sm text-gray-500">
                      {result.timestamp && new Date(result.timestamp).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="text-gray-700 mb-4">{result.content}</p>

                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div className="border-t pt-4">
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Metadata</h4>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(result.metadata).map(([key, value]) => (
                          <span
                            key={key}
                            className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded"
                          >
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {result.score !== undefined && (
                    <div className="mt-4 text-sm text-gray-500">
                      Relevance: {(result.score * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

### Prompt Building Interface
```typescript
// pages/memory/PromptBuilder.tsx
import React, { useState } from 'react';
import { useMemoryStore } from '../../store/memory';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

export const PromptBuilder: React.FC = () => {
  const { buildPrompt } = useMemoryStore();
  const [promptRequest, setPromptRequest] = useState({
    user_id: '',
    conversation_context: '',
    role: 'assistant',
    task_description: '',
    additional_context: ''
  });
  const [builtPrompt, setBuiltPrompt] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);

  const handleBuildPrompt = async () => {
    setIsBuilding(true);
    try {
      const response = await buildPrompt(promptRequest);
      setBuiltPrompt(response.prompt);
    } catch (error) {
      console.error('Failed to build prompt:', error);
    } finally {
      setIsBuilding(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Prompt Builder</h1>
        <p className="text-gray-600">Build contextual prompts with memory integration</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Build Prompt</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">User ID</label>
            <input
              type="text"
              value={promptRequest.user_id}
              onChange={(e) => setPromptRequest({ ...promptRequest, user_id: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              placeholder="Enter user ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Role</label>
            <select
              value={promptRequest.role}
              onChange={(e) => setPromptRequest({ ...promptRequest, role: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            >
              <option value="assistant">Assistant</option>
              <option value="parent">Parent</option>
              <option value="teenager">Teenager</option>
              <option value="child">Child</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Conversation Context</label>
            <Textarea
              value={promptRequest.conversation_context}
              onChange={(e) => setPromptRequest({ ...promptRequest, conversation_context: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              rows={3}
              placeholder="Enter conversation context"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Task Description</label>
            <Textarea
              value={promptRequest.task_description}
              onChange={(e) => setPromptRequest({ ...promptRequest, task_description: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              rows={2}
              placeholder="Describe what the AI should do"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Additional Context</label>
            <Textarea
              value={promptRequest.additional_context}
              onChange={(e) => setPromptRequest({ ...promptRequest, additional_context: e.target.value })}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              rows={2}
              placeholder="Any additional context or instructions"
            />
          </div>

          <Button
            onClick={handleBuildPrompt}
            disabled={isBuilding || !promptRequest.user_id}
            className="w-full"
          >
            {isBuilding ? 'Building...' : 'Build Prompt'}
          </Button>
        </div>
      </div>

      {builtPrompt && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Built Prompt</h2>

          <div className="bg-gray-50 p-4 rounded-md">
            <pre className="whitespace-pre-wrap text-sm text-gray-800">
              {builtPrompt}
            </pre>
          </div>

          <div className="mt-4 flex gap-2">
            <Button
              onClick={() => navigator.clipboard.writeText(builtPrompt)}
              variant="secondary"
            >
              Copy to Clipboard
            </Button>
            <Button
              onClick={() => {
                const blob = new Blob([builtPrompt], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'prompt.txt';
                a.click();
                URL.revokeObjectURL(url);
              }}
              variant="secondary"
            >
              Download
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Family Management Features

### Family Members Management
```typescript
// pages/family/FamilyMembers.tsx
import React, { useState } from 'react';
import { useFamilyMembers, useCreateFamilyMember, useUpdateFamilyMember, useDeleteFamilyMember } from '../../hooks/api/useFamilyMembers';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';

export const FamilyMembers: React.FC = () => {
  const { data: members, isLoading } = useFamilyMembers();
  const createMutation = useCreateFamilyMember();
  const updateMutation = useUpdateFamilyMember();
  const deleteMutation = useDeleteFamilyMember();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);

  const handleCreateMember = async (memberData: CreateMemberRequest) => {
    await createMutation.mutateAsync(memberData);
    setShowCreateModal(false);
  };

  const handleUpdateMember = async (memberData: UpdateMemberRequest) => {
    await updateMutation.mutateAsync(memberData);
    setShowEditModal(false);
    setSelectedMember(null);
  };

  const handleDeleteMember = async (memberId: string) => {
    if (window.confirm('Are you sure you want to delete this family member?')) {
      await deleteMutation.mutateAsync(memberId);
    }
  };

  if (isLoading) {
    return <div>Loading family members...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Family Members</h1>
          <p className="text-gray-600">Manage family members and permissions</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Add Member
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {members?.map((member) => (
          <div key={member.id} className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                {member.first_name?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-gray-900">
                  {member.first_name} {member.last_name}
                </h3>
                <p className="text-sm text-gray-500">{member.role}</p>
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center text-sm text-gray-600">
                <span className="font-medium">Email:</span>
                <span className="ml-2">{member.email || 'Not set'}</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <span className="font-medium">Phone:</span>
                <span className="ml-2">{member.phone || 'Not set'}</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <span className="font-medium">Age Group:</span>
                <span className="ml-2">{member.age_group || 'Not set'}</span>
              </div>
            </div>

            <div className="mt-4 flex justify-between items-center">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                member.is_active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {member.is_active ? 'Active' : 'Inactive'}
              </span>

              <div className="flex space-x-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setSelectedMember(member);
                    setShowEditModal(true);
                  }}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => handleDeleteMember(member.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Member Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add Family Member"
      >
        <FamilyMemberForm
          onSubmit={handleCreateMember}
          onCancel={() => setShowCreateModal(false)}
          isLoading={createMutation.isLoading}
        />
      </Modal>

      {/* Edit Member Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        title="Edit Family Member"
      >
        <FamilyMemberForm
          initialData={selectedMember}
          onSubmit={handleUpdateMember}
          onCancel={() => setShowEditModal(false)}
          isLoading={updateMutation.isLoading}
        />
      </Modal>
    </div>
  );
};

const FamilyMemberForm: React.FC<{
  initialData?: any;
  onSubmit: (data: any) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}> = ({ initialData, onSubmit, onCancel, isLoading }) => {
  const [formData, setFormData] = useState({
    first_name: initialData?.first_name || '',
    last_name: initialData?.last_name || '',
    email: initialData?.email || '',
    phone: initialData?.phone || '',
    role: initialData?.role || 'member',
    age_group: initialData?.age_group || '',
    is_active: initialData?.is_active ?? true,
    ...initialData
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">First Name</label>
          <input
            type="text"
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Last Name</label>
          <input
            type="text"
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Phone</label>
        <input
          type="tel"
          value={formData.phone}
          onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Role</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          >
            <option value="parent">Parent</option>
            <option value="grandparent">Grandparent</option>
            <option value="teenager">Teenager</option>
            <option value="child">Child</option>
            <option value="member">Member</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Age Group</label>
          <select
            value={formData.age_group}
            onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
          >
            <option value="">Select age group</option>
            <option value="child">Child (0-12)</option>
            <option value="teenager">Teenager (13-17)</option>
            <option value="adult">Adult (18+)</option>
          </select>
        </div>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          checked={formData.is_active}
          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
          Active
        </label>
      </div>

      <div className="flex justify-end space-x-2">
        <Button
          type="button"
          variant="secondary"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </form>
  );
};
```

### Parental Controls Interface
```typescript
// pages/family/ParentalControls.tsx
import React, { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Toggle } from '../../components/ui/Toggle';

export const ParentalControls: React.FC = () => {
  const [selectedChild, setSelectedChild] = useState('');
  const [controls, setControls] = useState({
    screen_time_limits: {
      daily_minutes: 120,
      allowed_hours: {
        start: '09:00',
        end: '21:00'
      }
    },
    content_filtering: {
      enabled: true,
      blocked_keywords: [],
      blocked_domains: [],
      allowed_domains: []
    },
    app_restrictions: {
      social_media: false,
      gaming: false,
      messaging: true
    },
    privacy_settings: {
      location_sharing: false,
      camera_access: false,
      microphone_access: false
    }
  });

  const handleSaveControls = async () => {
    try {
      await api.post(`/family/parental-controls/${selectedChild}`, controls);
      // Show success message
    } catch (error) {
      console.error('Failed to save parental controls:', error);
      // Show error message
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Parental Controls</h1>
        <p className="text-gray-600">Manage screen time, content filtering, and privacy settings</p>
      </div>

      {/* Child Selection */}
      <div className="bg-white p-6 rounded-lg shadow">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Child</label>
        <select
          value={selectedChild}
          onChange={(e) => setSelectedChild(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
        >
          <option value="">Select a child to manage</option>
          {/* This would be populated with actual children */}
          <option value="child1">Child One</option>
          <option value="child2">Child Two</option>
        </select>
      </div>

      {selectedChild && (
        <>
          {/* Screen Time Limits */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Screen Time Limits</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Daily Limit (minutes)</label>
                <input
                  type="number"
                  value={controls.screen_time_limits.daily_minutes}
                  onChange={(e) => setControls({
                    ...controls,
                    screen_time_limits: {
                      ...controls.screen_time_limits,
                      daily_minutes: parseInt(e.target.value)
                    }
                  })}
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Allowed Hours</label>
                <div className="grid grid-cols-2 gap-4 mt-1">
                  <div>
                    <label className="block text-xs text-gray-500">Start Time</label>
                    <input
                      type="time"
                      value={controls.screen_time_limits.allowed_hours.start}
                      onChange={(e) => setControls({
                        ...controls,
                        screen_time_limits: {
                          ...controls.screen_time_limits,
                          allowed_hours: {
                            ...controls.screen_time_limits.allowed_hours,
                            start: e.target.value
                          }
                        }
                      })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500">End Time</label>
                    <input
                      type="time"
                      value={controls.screen_time_limits.allowed_hours.end}
                      onChange={(e) => setControls({
                        ...controls,
                        screen_time_limits: {
                          ...controls.screen_time_limits,
                          allowed_hours: {
                            ...controls.screen_time_limits.allowed_hours,
                            end: e.target.value
                          }
                        }
                      })}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Content Filtering */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Content Filtering</h2>

            <div className="space-y-4">
              <div className="flex items-center">
                <Toggle
                  checked={controls.content_filtering.enabled}
                  onChange={(checked) => setControls({
                    ...controls,
                    content_filtering: {
                      ...controls.content_filtering,
                      enabled: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Enable Content Filtering
                </label>
              </div>

              {controls.content_filtering.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Blocked Keywords</label>
                    <textarea
                      value={controls.content_filtering.blocked_keywords.join('\n')}
                      onChange={(e) => setControls({
                        ...controls,
                        content_filtering: {
                          ...controls.content_filtering,
                          blocked_keywords: e.target.value.split('\n').filter(word => word.trim())
                        }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                      rows={3}
                      placeholder="Enter blocked keywords (one per line)"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Blocked Domains</label>
                    <textarea
                      value={controls.content_filtering.blocked_domains.join('\n')}
                      onChange={(e) => setControls({
                        ...controls,
                        content_filtering: {
                          ...controls.content_filtering,
                          blocked_domains: e.target.value.split('\n').filter(domain => domain.trim())
                        }
                      })}
                      className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                      rows={3}
                      placeholder="Enter blocked domains (one per line)"
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* App Restrictions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">App Restrictions</h2>

            <div className="space-y-3">
              <div className="flex items-center">
                <Toggle
                  checked={controls.app_restrictions.social_media}
                  onChange={(checked) => setControls({
                    ...controls,
                    app_restrictions: {
                      ...controls.app_restrictions,
                      social_media: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Social Media Apps
                </label>
              </div>

              <div className="flex items-center">
                <Toggle
                  checked={controls.app_restrictions.gaming}
                  onChange={(checked) => setControls({
                    ...controls,
                    app_restrictions: {
                      ...controls.app_restrictions,
                      gaming: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Gaming Apps
                </label>
              </div>

              <div className="flex items-center">
                <Toggle
                  checked={controls.app_restrictions.messaging}
                  onChange={(checked) => setControls({
                    ...controls,
                    app_restrictions: {
                      ...controls.app_restrictions,
                      messaging: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Messaging Apps
                </label>
              </div>
            </div>
          </div>

          {/* Privacy Settings */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Privacy Settings</h2>

            <div className="space-y-3">
              <div className="flex items-center">
                <Toggle
                  checked={controls.privacy_settings.location_sharing}
                  onChange={(checked) => setControls({
                    ...controls,
                    privacy_settings: {
                      ...controls.privacy_settings,
                      location_sharing: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Location Sharing
                </label>
              </div>

              <div className="flex items-center">
                <Toggle
                  checked={controls.privacy_settings.camera_access}
                  onChange={(checked) => setControls({
                    ...controls,
                    privacy_settings: {
                      ...controls.privacy_settings,
                      camera_access: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Camera Access
                </label>
              </div>

              <div className="flex items-center">
                <Toggle
                  checked={controls.privacy_settings.microphone_access}
                  onChange={(checked) => setControls({
                    ...controls,
                    privacy_settings: {
                      ...controls.privacy_settings,
                      microphone_access: checked
                    }
                  })}
                />
                <label className="ml-2 text-sm font-medium text-gray-700">
                  Microphone Access
                </label>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSaveControls}>
              Save Controls
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
```

---

## Dashboard & Analytics

### Real-time Dashboard
```typescript
// pages/dashboard/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../store/auth';
import { api } from '../../lib/api';

interface DashboardWidget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'card';
  title: string;
  data: any;
  position: { x: number; y: number; width: number; height: number };
}

export const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [widgets, setWidgets] = useState<DashboardWidget[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    if (!user) return;

    // Fetch initial widgets
    fetchWidgets();

    // Establish WebSocket connection
    const websocket = new WebSocket(`ws://localhost:8001/ws/dashboard`);

    websocket.onopen = () => {
      console.log('Dashboard WebSocket connected');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'widget_update') {
        setWidgets(prev =>
          prev.map(widget =>
            widget.id === data.widget_id
              ? { ...widget, data: data.data }
              : widget
          )
        );
      } else if (data.type === 'system_metrics') {
        // Update system metrics
        updateSystemMetrics(data.data);
      }
    };

    websocket.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [user]);

  const fetchWidgets = async () => {
    try {
      const response = await api.get('/dashboard/widgets');
      setWidgets(response.data);
    } catch (error) {
      console.error('Failed to fetch widgets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSystemMetrics = (metrics: any) => {
    // Update system metrics in real-time
    setWidgets(prev =>
      prev.map(widget => {
        if (widget.type === 'metric' && widget.id === 'system-status') {
          return { ...widget, data: metrics };
        }
        return widget;
      })
    );
  };

  const renderWidget = (widget: DashboardWidget) => {
    switch (widget.type) {
      case 'card':
        return <MetricCard widget={widget} />;
      case 'chart':
        return <ChartWidget widget={widget} />;
      case 'table':
        return <TableWidget widget={widget} />;
      default:
        return <div>Unknown widget type</div>;
    }
  };

  if (!user) {
    return <div>Please log in to view the dashboard</div>;
  }

  if (isLoading) {
    return <div>Loading dashboard...</div>;
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user.first_name}!
          </h1>
          <p className="text-gray-600">Here's what's happening with your family assistant</p>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className="bg-white p-6 rounded-lg shadow"
            style={{
              gridColumn: `span ${widget.position.width}`,
              gridRow: `span ${widget.position.height}`
            }}
          >
            {renderWidget(widget)}
          </div>
        ))}
      </div>
    </div>
  );
};

const MetricCard: React.FC<{ widget: DashboardWidget }> = ({ widget }) => {
  const { title, data } = widget;

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <div className="text-3xl font-bold text-blue-600">
        {data.value}
      </div>
      <div className="text-sm text-gray-500 mt-1">
        {data.description}
      </div>
      {data.trend && (
        <div className="flex items-center mt-2">
          <span className={`text-sm ${
            data.trend > 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {data.trend > 0 ? '↑' : '↓'} {Math.abs(data.trend)}%
          </span>
          <span className="text-xs text-gray-500 ml-1">vs last week</span>
        </div>
      )}
    </div>
  );
};

const ChartWidget: React.FC<{ widget: DashboardWidget }> = ({ widget }) => {
  const { title, data } = widget;

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="h-48 flex items-center justify-center bg-gray-50 rounded">
        <p className="text-gray-500">Chart: {data.chartType}</p>
      </div>
    </div>
  );
};

const TableWidget: React.FC<{ widget: DashboardWidget }> = ({ widget }) => {
  const { title, data } = widget;

  return (
    <div>
      <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {data.headers?.map((header: string) => (
                <th key={header} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.rows?.map((row: any[], index: number) => (
              <tr key={index}>
                {row.map((cell: any, cellIndex: number) => (
                  <td key={cellIndex} className="px-4 py-2 text-sm text-gray-900">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

---

## UI Components & Design System

### Base UI Components
```typescript
// components/ui/Button.tsx
import React from 'react';
import { cn } from '../../lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  className,
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    outline: 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:ring-blue-500'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 0-2 0H4a2 2 0 00-2 0v12a2 2 0 002 2h2a2 2 0 002-2h.586a1 1 0 00.707-.293z"
          />
        </svg>
      )}
      {children}
    </button>
  );
};

// components/ui/Modal.tsx
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md'
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl'
  };

  return createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div
        ref={modalRef}
        className={`${sizeClasses[size]} w-full bg-white rounded-lg shadow-xl`}
      >
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
};

// components/ui/Toggle.tsx
import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
}

export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  disabled = false,
  label
}) => {
  return (
    <div className="flex items-center">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${checked ? 'bg-blue-600' : 'bg-gray-200'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
            ${checked ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
      {label && (
        <span className="ml-3 text-sm font-medium text-gray-700">{label}</span>
      )}
    </div>
  );
};
```

### Form Components
```typescript
// components/ui/Input.tsx
import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  className,
  ...props
}) => {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
          focus:outline-none focus:ring-blue-500 focus:border-blue-500
          ${error ? 'border-red-500' : ''}
          ${className}
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// components/ui/Select.tsx
interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  label?: string;
  error?: string;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onChange,
  options,
  placeholder,
  label,
  error,
}) => {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
          focus:outline-none focus:ring-blue-500 focus:border-blue-500
          ${error ? 'border-red-500' : ''}
        `}
      >
        {placeholder && (
          <option value="">{placeholder}</option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// components/ui/Textarea.tsx
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  className,
  ...props
}) => {
  return (
    <div>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <textarea
        className={`
          block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm
          focus:outline-none focus:ring-blue-500 focus:border-blue-500
          ${error ? 'border-red-500' : ''}
          ${className}
        `}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};
```

---

## Real-time Features

### WebSocket Integration
```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import { useAuthStore } from '../store/auth';

interface WebSocketMessage {
  type: string;
  data: any;
}

export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    if (!accessToken) return;

    const wsUrl = `${url}?token=${accessToken}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        setLastMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
        setError('Invalid message format');
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = (event) => {
      setError('WebSocket connection error');
      console.error('WebSocket error:', event);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [url, accessToken]);

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage
  };
};

// hooks/useDashboardWebSocket.ts
import { useWebSocket } from './useWebSocket';

export const useDashboardWebSocket = () => {
  return useWebSocket('ws://localhost:8001/ws/dashboard');
};

// hooks/useChatWebSocket.ts
import { useWebSocket } from './useWebSocket';

export const useChatWebSocket = (conversationId: string) => {
  return useWebSocket(`ws://localhost:8001/ws/chat/${conversationId}`);
};
```

### Real-time Updates Component
```typescript
// components/RealTimeStatus.tsx
import React from 'react';
import { useDashboardWebSocket } from '../../hooks/useDashboardWebSocket';

export const RealTimeStatus: React.FC = () => {
  const { isConnected, lastMessage } = useDashboardWebSocket();

  return (
    <div className="flex items-center space-x-2">
      <div
        className={`w-3 h-3 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span className="text-sm text-gray-600">
        {isConnected ? 'Connected' : 'Disconnected'}
      </span>
      {lastMessage && (
        <span className="text-xs text-gray-500">
          Last update: {new Date(lastMessage.timestamp).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

// components/NotificationProvider.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-hot-toast';

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: crypto.randomUUID(),
      timestamp: new Date(),
      read: false
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 49)]);

    // Show toast notification
    switch (notification.type) {
      case 'success':
        toast.success(notification.message);
        break;
      case 'error':
        toast.error(notification.message);
        break;
      case 'info':
        toast(notification.message);
        break;
      case 'warning':
        toast(notification.message);
        break;
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notification =>
        notification.id === id ? { ...notification, read: true } : notification
      )
    );
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return (
    <NotificationContext.Provider value={{
      notifications,
      addNotification,
      markAsRead,
      clearAll
    }}>
      {children}
      <ToastContainer position="top-right" />
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};
```

---

## Error Handling & User Experience

### Error Boundary
```typescript
// components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H9a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2v-4.172a2 2 0 00-2.002-2z" />
              </svg>
            </div>

            <h1 className="text-xl font-bold text-gray-900 mb-2">
              Something went wrong
            </h1>

            <p className="text-gray-600 mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>

            <details className="mb-4 text-left">
              <summary className="cursor-pointer text-sm text-gray-500">
                Error Details
              </summary>
              <pre className="mt-2 p-4 bg-gray-100 rounded text-xs text-left overflow-x-auto">
                {this.state.error?.stack}
              </pre>
            </details>

            <button
              onClick={this.handleReset}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Loading States
```typescript
// components/SuspenseWrapper.tsx
import React, { Suspense } from 'react';
import { LoadingState } from './ui/LoadingState';
import { ErrorState } from './ui/ErrorState';

interface SuspenseWrapperProps {
  fallback?: ReactNode;
  error?: ReactNode;
  children: React.ReactNode;
}

export const SuspenseWrapper: React.FC<SuspenseWrapperProps> = ({
  fallback = <LoadingState />,
  error = <ErrorState />,
  children
}) => (
  <ErrorBoundary>
    <Suspense fallback={fallback}>
      {children}
    </Suspense>
  </ErrorBoundary>
);
};

// components/PageTransition.tsx
import React from 'react';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  className = ''
}) => {
  return (
    <div
      className={`animate-in fade-in duration-300 ${className}`}
    >
      {children}
    </div>
  );
};
```

---

## Testing Strategy

### Test Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  testEnvironment: 'jsdom',
  setupFiles: ['./src/test/setup.ts'],
});

// src/test/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock API
vi.mock('../../lib/api', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn()
}));

// Mock WebSocket
vi.mock('../hooks/useWebSocket', () => ({
  isConnected: vi.fn(() => true),
  lastMessage: vi.fn(() => null),
  error: vi.fn(() => null),
  sendMessage: vi.fn()
}));
```

### Component Tests
```typescript
// src/components/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from '../Button';

describe('Button', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Click me');
  });

  it('applies variant styles correctly', () => {
    render(<Button variant="danger">Delete</Button>);

    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-red-600');
  });

  it('handles loading state', () => {
    render(<Button isLoading>Submit</Button>);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('calls onClick handler when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole('button');
    await fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

// src/hooks/__tests__/useAuthStore.test.ts
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../auth';

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false
    });
  });

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useAuthStore());

    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
    expect(result.current.refreshToken).toBeNull();
  });

  it('updates user state on login', async () => {
    const { result } = renderHook(() => useAuthStore());

    const mockUser = {
      id: '1',
      first_name: 'John',
      email: 'john@example.com',
      role: 'parent'
    };

    await act(async () => {
      result.current.login({
        username: 'john@example.com',
        password: 'password'
      });
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.accessToken).toBeTruthy();
  });
});
```

### Integration Tests
```typescript
// tests/integration/auth.test.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Authentication', () => {
  test('user can login successfully', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto('/login');
    await loginPage.login('test@example.com', 'password123');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Should show user's name in header
    await expect(page.locator('text=Welcome, Test')).toBeVisible();
  });

  test('user sees appropriate navigation based on role', async ({ page }) => {
    const loginPage = new LoginPage(page);

    // Login as parent
    await page.goto('/login');
    await loginPage.login('parent@example.com', 'password123');

    // Should see admin navigation items
    await expect(page.locator('text=Family Management')).toBeVisible();
    await expect(page.locator(text=MCP Admin)).toBeVisible();

    // Login as child
    await page.goto('/login');
    await loginPage.login('child@example.com', 'password123');

    // Should not see admin navigation items
    await expect(page.locator('text=Family Management')).not.toBeVisible();
    await expect(page.locator(text=MCP Admin)).not.toBeVisible();
  });
});
```

---

## Deployment Considerations

### Environment Configuration
```typescript
// src/config/environment.ts
export const config = {
  development: {
    apiUrl: 'http://localhost:8001',
    wsUrl: 'ws://localhost:8001/ws'
  },
  production: {
    apiUrl: import.meta.env.VITE_API_URL || 'https://family-assistant.homelab.pesulabs.net',
    wsUrl: import.meta.env.VITE_WS_URL || 'wss://family-assistant.homelab.pesulabs.net/ws'
  }
};

export const env = config[import.meta.env.MODE as keyof typeof config];
```

### Build Configuration
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@hooks': resolve(__dirname, './src/hooks'),
      '@lib': resolve(__dirname, './src/lib'),
      '@types': resolve(__dirname, './src/types')
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: env.apiUrl,
        changeOrigin: true
      },
      '/ws': {
        target: env.wsUrl,
        ws: true
      }
    }
  }
});
```

### Docker Configuration
```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Build the application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: family-assistant-frontend
  namespace: homelab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: family-assistant-frontend
  template:
    metadata:
      labels:
        app: family-assistant-frontend
    spec:
      containers:
      - name: frontend
        image: family-assistant-frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_URL
          value: "http://family-assistant-backend.homelab.svc.cluster.local:8001"
        - name: VITE_WS_URL
          value: "ws://family-assistant-backend.homelab.svc.cluster.local:8001/ws"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: family-assistant-frontend
  namespace: homelab
spec:
  selector:
    app: family-assistant-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

---

This comprehensive documentation provides a complete guide for implementing the Family Assistant frontend, covering all major features from authentication to MCP system integration, with code examples, component structures, and deployment configurations.

The guide follows best practices for:
- **Security**: JWT authentication with proper token management
- **Performance**: Optimized component rendering and state management
- **User Experience**: Comprehensive error handling and loading states
- **Maintainability**: Clean component architecture and separation of concerns
- **Scalability**: Efficient state management and data fetching patterns
- **Accessibility**: Proper ARIA labels and semantic HTML
- **Testing**: Comprehensive test coverage from unit to integration

Each section includes practical, copy-pasteable code examples that can be directly used in your implementation.