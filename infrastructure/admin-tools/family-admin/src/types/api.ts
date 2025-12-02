/**
 * API Type Definitions
 *
 * Shared TypeScript types for API requests and responses
 * Used by both API routes (server) and React components (client)
 *
 * Agent Note: Import these types in both route handlers and components
 * for type safety and autocomplete
 */

// ============================================
// Common Types
// ============================================

export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
  timestamp: string;
}

export interface ApiError {
  error: string;
  code?: string;
  statusCode: number;
  details?: any;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// ============================================
// Health & Status
// ============================================

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  timestamp: string;
  uptime: number;
  responseTime: string;
  services: {
    [key: string]: ServiceHealth;
  };
  environment?: string;
}

export interface ServiceHealth {
  healthy: boolean;
  message: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  timestamp: string;
  services: {
    [key: string]: ServiceHealth;
  };
}

// ============================================
// Chat
// ============================================

export interface ChatRequest {
  message: string;
  userId?: string;
  sessionId?: string;
  stream?: boolean;
}

export interface ChatResponse {
  response: string;
  sessionId: string;
  timestamp: string;
  model?: string;
  usage?: TokenUsage;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

// ============================================
// LLM Direct Access
// ============================================

export interface LLMChatRequest {
  message: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  conversation_history?: ChatMessage[];
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface LLMChatResponse {
  response: string;
  model: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  finish_reason: string;
}

// ============================================
// Family Members
// ============================================

export type FamilyRole = 'parent' | 'child' | 'teen' | 'grandparent';

export interface FamilyMember {
  id: string;
  name: string;
  role: FamilyRole;
  age?: number;
  preferences?: FamilyMemberPreferences;
  created_at: string;
  updated_at: string;
}

export interface FamilyMemberPreferences {
  language?: string;
  timezone?: string;
  notifications?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  [key: string]: any;
}

export interface CreateFamilyMemberRequest {
  name: string;
  role: FamilyRole;
  age?: number;
  preferences?: FamilyMemberPreferences;
}

export interface UpdateFamilyMemberRequest {
  name?: string;
  role?: FamilyRole;
  age?: number;
  preferences?: FamilyMemberPreferences;
}

export interface FamilyMembersResponse {
  members: FamilyMember[];
}

// ============================================
// Family Assistant Features
// ============================================

export interface FamilyTask {
  id: string;
  title: string;
  description?: string;
  assignedTo: string;
  dueDate?: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
}

export interface FamilyEvent {
  id: string;
  title: string;
  description?: string;
  startTime: string;
  endTime?: string;
  location?: string;
  attendees: string[];
  reminders?: string[];
  created_at: string;
}

export interface FamilyNotification {
  id: string;
  type: 'info' | 'warning' | 'success' | 'error';
  title: string;
  message: string;
  targetMembers: string[];
  read: boolean;
  timestamp: string;
}

// ============================================
// Home Assistant Integration
// ============================================

export interface HomeAssistantConfig {
  enabled: boolean;
  url: string;
  accessToken?: string;
  entities: HomeAssistantEntities;
  voice_commands: VoiceCommandConfig;
}

export interface HomeAssistantEntities {
  light_switches: string[];
  smart_speakers: string[];
  displays: string[];
  sensors: string[];
}

export interface VoiceCommandConfig {
  wake_word: string;
  confidence_threshold: number;
  custom_commands: VoiceCommand[];
}

export interface VoiceCommand {
  id: string;
  phrase: string;
  intent: string;
  entities: Record<string, any>;
  response_template?: string;
  ha_service?: string;
}

// ============================================
// API Client Helpers
// ============================================

/**
 * Type-safe fetch wrapper for API routes
 *
 * @example
 * const result = await apiRequest<ChatResponse>('/api/family/chat', {
 *   method: 'POST',
 *   body: { message: 'Hello' }
 * });
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options?: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    body?: any;
    headers?: Record<string, string>;
  }
): Promise<T> {
  const response = await fetch(endpoint, {
    method: options?.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: options?.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.error || 'API request failed');
  }

  return response.json();
}

/**
 * Type-safe GET request
 */
export async function apiGet<T = any>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'GET' });
}

/**
 * Type-safe POST request
 */
export async function apiPost<T = any>(endpoint: string, body: any): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'POST', body });
}

/**
 * Type-safe PUT request
 */
export async function apiPut<T = any>(endpoint: string, body: any): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'PUT', body });
}

/**
 * Type-safe DELETE request
 */
export async function apiDelete<T = any>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'DELETE' });
}
