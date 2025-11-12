/**
 * API Configuration and Utilities
 *
 * Centralized API configuration that works in both development and production.
 * Uses environment variables with sensible fallbacks.
 */

// Get base API URL from environment or use current origin
const getApiBaseUrl = (): string => {
  // In production (when served from same origin as API)
  if (import.meta.env.PROD) {
    return window.location.origin;
  }

  // In development, use environment variable or fallback to NodePort
  return import.meta.env.VITE_API_BASE_URL || 'http://100.81.76.55:30801';
};

// Get WebSocket URL from environment or derive from HTTP URL
const getWebSocketUrl = (): string => {
  const apiBase = getApiBaseUrl();

  // In production (HTTPS), use WSS
  if (apiBase.startsWith('https://')) {
    return apiBase.replace('https://', 'wss://') + '/ws';
  }

  // In development or HTTP, use WS
  return apiBase.replace('http://', 'ws://') + '/ws';
};

export const API_BASE_URL = getApiBaseUrl();
export const WS_URL = getWebSocketUrl();

/**
 * Fetch wrapper with automatic base URL prepending
 */
export async function apiFetch(
  endpoint: string,
  options?: RequestInit
): Promise<Response> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
}

/**
 * Typed API response wrapper
 */
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await apiFetch(endpoint, options);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
}

// Export commonly used endpoints
export const API_ENDPOINTS = {
  // Health & System
  health: '/health',
  systemMetrics: '/dashboard/system-health',

  // Dashboard
  dashboardHealth: '/dashboard/system-health',

  // Services (legacy compatibility)
  legacyHealth: '/api/health',
  legacyMetrics: '/api/system/metrics',
  legacyServices: '/api/system/services',
} as const;
