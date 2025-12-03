/**
 * API Client for Family Assistant Backend
 *
 * Handles authentication, token management, and API calls to the FastAPI backend.
 */

// Use Next.js API routes as proxy to avoid CORS and SSL certificate issues
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/backend';

export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  is_admin: boolean;
  display_name: string;
  first_name: string;
  last_name: string;
}

export interface DashboardHealth {
  status: string;
  components: Record<string, { status: string; message?: string }>;
  timestamp: string;
}

// ==============================================================================
// Phase 2: Extended Types for Memory & Prompt System
// ==============================================================================

export interface Phase2UserProfile extends UserProfile {
  role: 'parent' | 'teenager' | 'child' | 'grandparent' | 'member';
  language_preference: 'en' | 'es';
  age_group?: string;
  parental_controls?: ParentalControls;
}

// Memory Types
export interface MemorySearchRequest {
  query: string;
  user_id: string;
  limit?: number;
  context_window?: number;
}

export interface Memory {
  id: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
  source: 'redis' | 'mem0' | 'postgres' | 'qdrant' | 'archive';
  relevance_score?: number;
}

export interface MemorySearchResult {
  results: Memory[];
  total: number;
  sources: string[];
}

// Prompt Types
export interface PromptBuildRequest {
  user_id: string;
  conversation_id: string;
  minimal?: boolean;
}

export interface PromptResponse {
  system_prompt: string;
  context: string;
  metadata: {
    role: string;
    language: string;
    layers: string[];
  };
  prompt?: string;  // For core/role prompts
  length?: number;
  estimated_tokens?: number;
}

// Family Member Management
export interface FamilyMember {
  id: string;
  name: string;
  email: string;
  role: 'parent' | 'teenager' | 'child' | 'grandparent';
  avatar?: string;
  language_preference: 'en' | 'es';
  parental_controls?: ParentalControls;
  created_at: string;
  last_active?: string;
}

export interface ParentalControls {
  safe_search: boolean;
  content_filter: 'strict' | 'moderate' | 'off';
  screen_time_daily: number;
  screen_time_weekend: number;
  allowed_apps: string[];
  blocked_keywords: string[];
}

// Knowledge Base
export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  contributors: string[];
  created_at: string;
  updated_at: string;
}

// Activity Reports
export interface ActivityReport {
  user_id: string;
  user_name: string;
  date: string;
  queries: number;
  screen_time_hours: number;
  topics: string[];
  sentiment?: 'positive' | 'neutral' | 'negative';
}

// System Health
export interface Phase2Health {
  status: 'healthy' | 'degraded' | 'unhealthy';
  redis: { connected: boolean; latency_ms: number };
  mem0: { connected: boolean; status: string };
  qdrant: { connected: boolean; collections: number };
  ollama: { connected: boolean; models: string[] };
  timestamp: string;
}

// System Statistics
export interface SystemStats {
  total_memories: number;
  memories_by_layer: Record<string, number>;
  total_users: number;
  active_conversations: number;
  storage_usage_mb: number;
  cache_hit_rate: number;
}

// Chat Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface SendMessageRequest {
  message: string;
  conversation_id: string;
  user_id?: string;
}

export interface SendMessageResponse {
  response: string;
  conversation_id: string;
  metadata?: Record<string, any>;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    // Load token from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'An error occurred'
      }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Login with email and password (deprecated - using Authentik SSO)
   * This method is kept for backward compatibility but should not be used in production
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    // In production with Authentik, login is handled by SSO
    // This method is only used for development
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 Development mode: Simulating login');
      const mockToken: TokenResponse = {
        access_token: 'dev-token-' + Date.now(),
        token_type: 'Bearer',
        expires_in: 3600,
      };
      this.setToken(mockToken.access_token);
      return mockToken;
    }

    throw new Error('Login is handled by Authentik SSO. Please access the application through the authenticated URL.');
  }

  /**
   * Get current user profile from Authentik headers
   */
  async getProfile(): Promise<UserProfile> {
    // Use the frontend API endpoint that reads Authentik headers
    const response = await fetch('/api/auth/me', {
      headers: {
        // Forward any existing auth headers for development
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: 'Failed to get profile'
      }));
      throw new Error(error.error || 'Profile fetch failed');
    }

    return response.json();
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<TokenResponse> {
    return this.request<TokenResponse>('/api/v1/auth/refresh', {
      method: 'POST',
    });
  }

  /**
   * Logout (client-side only - clear token)
   */
  logout() {
    this.clearToken();
  }

  /**
   * Get dashboard health status
   */
  async getDashboardHealth(): Promise<DashboardHealth> {
    return this.request<DashboardHealth>('/health');
  }

  // ==============================================================================
  // Phase 2: Memory Management
  // ==============================================================================

  /**
   * Search memories across all layers
   */
  async searchMemories(request: MemorySearchRequest): Promise<MemorySearchResult> {
    return this.request<MemorySearchResult>('/api/phase2/memory/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Save conversation context to memory
   */
  async saveContext(conversationId: string, context: string, userId: string): Promise<void> {
    return this.request<void>('/api/phase2/memory/save', {
      method: 'POST',
      body: JSON.stringify({
        conversation_id: conversationId,
        context,
        user_id: userId
      }),
    });
  }

  /**
   * Get conversation context from memory
   */
  async getConversationContext(conversationId: string): Promise<Memory[]> {
    return this.request<Memory[]>(`/api/phase2/memory/context/${conversationId}`);
  }

  // ==============================================================================
  // Phase 2: Prompt System
  // ==============================================================================

  /**
   * Build dynamic prompt for user
   */
  async buildPrompt(request: PromptBuildRequest): Promise<PromptResponse> {
    return this.request<PromptResponse>('/api/phase2/prompts/build', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get role-specific prompt
   */
  async getRolePrompt(role: string): Promise<{ prompt: string }> {
    return this.request<{ prompt: string }>(`/api/phase2/prompts/role/${role}`);
  }

  /**
   * Get core system prompt
   */
  async getCorePrompt(): Promise<{ prompt: string }> {
    return this.request<{ prompt: string }>('/api/phase2/prompts/core');
  }

  // ==============================================================================
  // Phase 2: User Management
  // ==============================================================================

  /**
   * Get Phase 2 user profile with role and language preference
   */
  async getPhase2UserProfile(userId: string): Promise<Phase2UserProfile> {
    return this.request<Phase2UserProfile>(`/api/phase2/users/${userId}/profile`);
  }

  /**
   * Update user profile
   */
  async updateUserProfile(userId: string, profile: Partial<Phase2UserProfile>): Promise<Phase2UserProfile> {
    return this.request<Phase2UserProfile>(`/api/phase2/users/${userId}/profile`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
  }

  // ==============================================================================
  // Family Management (Backend endpoints needed)
  // ==============================================================================

  /**
   * Get all family members
   */
  async getFamilyMembers(): Promise<FamilyMember[]> {
    return this.request<FamilyMember[]>('/api/v1/family/members');
  }

  /**
   * Create a new family member
   */
  async createFamilyMember(member: Partial<FamilyMember>): Promise<FamilyMember> {
    return this.request<FamilyMember>('/api/v1/family/members', {
      method: 'POST',
      body: JSON.stringify(member),
    });
  }

  /**
   * Update family member details
   */
  async updateFamilyMember(memberId: string, updates: Partial<FamilyMember>): Promise<FamilyMember> {
    return this.request<FamilyMember>(`/api/v1/family/members/${memberId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete family member
   */
  async deleteFamilyMember(memberId: string): Promise<void> {
    return this.request<void>(`/api/v1/family/members/${memberId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Get parental controls for a family member
   */
  async getParentalControls(memberId: string): Promise<ParentalControls> {
    return this.request<ParentalControls>(`/api/v1/family/parental-controls/${memberId}`);
  }

  /**
   * Update parental controls
   */
  async updateParentalControls(memberId: string, controls: ParentalControls): Promise<void> {
    return this.request<void>(`/api/v1/family/parental-controls/${memberId}`, {
      method: 'PATCH',
      body: JSON.stringify(controls),
    });
  }

  // ==============================================================================
  // Knowledge Base (Backend endpoints needed)
  // ==============================================================================

  /**
   * Get knowledge items, optionally filtered by category
   */
  async getKnowledgeItems(category?: string): Promise<KnowledgeItem[]> {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request<KnowledgeItem[]>(`/api/knowledge${params}`);
  }

  /**
   * Create a new knowledge item
   */
  async createKnowledgeItem(item: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return this.request<KnowledgeItem>('/api/knowledge', {
      method: 'POST',
      body: JSON.stringify(item),
    });
  }

  /**
   * Update knowledge item
   */
  async updateKnowledgeItem(itemId: string, updates: Partial<KnowledgeItem>): Promise<KnowledgeItem> {
    return this.request<KnowledgeItem>(`/api/knowledge/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * Delete knowledge item
   */
  async deleteKnowledgeItem(itemId: string): Promise<void> {
    return this.request<void>(`/api/knowledge/${itemId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Search knowledge base
   */
  async searchKnowledge(query: string): Promise<KnowledgeItem[]> {
    return this.request<KnowledgeItem[]>(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
  }

  // ==============================================================================
  // Activity Reports (Backend endpoints needed)
  // ==============================================================================

  /**
   * Get activity reports for date range
   */
  async getActivityReports(startDate?: string, endDate?: string): Promise<ActivityReport[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const queryString = params.toString();
    return this.request<ActivityReport[]>(`/api/reports/activity${queryString ? `?${queryString}` : ''}`);
  }

  /**
   * Get activity report for specific user
   */
  async getUserActivityReport(userId: string, startDate?: string, endDate?: string): Promise<ActivityReport[]> {
    const params = new URLSearchParams({ user_id: userId });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return this.request<ActivityReport[]>(`/api/reports/activity?${params}`);
  }

  // ==============================================================================
  // System Health & Statistics
  // ==============================================================================

  /**
   * Get Phase 2 system health (memory services)
   * Uses frontend API route to avoid mixed content errors
   */
  async getPhase2Health(): Promise<Phase2Health> {
    const response = await fetch('/api/phase2/health');
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to fetch health status' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  }

  /**
   * Get system statistics
   * Uses frontend API route to avoid mixed content errors
   */
  async getSystemStats(): Promise<SystemStats> {
    const response = await fetch('/api/phase2/stats');
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Failed to fetch system stats' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // ==============================================================================
  // Chat Integration (Backend endpoints needed)
  // ==============================================================================

  /**
   * Send chat message
   */
  async sendChatMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    return this.request<SendMessageResponse>('/api/chat/send', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get chat history for conversation
   */
  async getChatHistory(conversationId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/api/chat/history/${conversationId}`);
  }

  /**
   * Clear chat history
   */
  async clearChatHistory(conversationId: string): Promise<void> {
    return this.request<void>(`/api/chat/history/${conversationId}`, {
      method: 'DELETE',
    });
  }

  // ==============================================================================
  // Sub-Agent Analytics
  // ==============================================================================

  /**
   * Get analytics overview (24h metrics, agent popularity, recent executions)
   */
  async getAnalyticsOverview(): Promise<any> {
    return this.request<any>('/api/v1/analytics/sub-agents/overview');
  }

  /**
   * Get detailed execution trace for a specific execution
   */
  async getExecutionTrace(executionId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/sub-agents/traces/${executionId}`);
  }

  // ==============================================================================
  // Chat Analytics (Loki-based)
  // ==============================================================================

  /**
   * Get chat analytics overview from Loki logs
   */
  async getChatAnalyticsOverview(timeRange: string = '24h'): Promise<any> {
    return this.request<any>(`/api/v1/analytics/chat/overview?range=${timeRange}`);
  }

  /**
   * Get raw chat session logs from Loki
   */
  async getChatLogs(limit: number = 50, timeRange: string = '24h'): Promise<any> {
    return this.request<any>(`/api/v1/analytics/chat/logs?limit=${limit}&range=${timeRange}`);
  }

  /**
   * Get token usage statistics by model from Loki
   */
  async getChatTokenStats(timeRange: string = '7d'): Promise<any> {
    return this.request<any>(`/api/v1/analytics/chat/tokens?range=${timeRange}`);
  }
}

// Singleton instance
export const apiClient = new ApiClient();
