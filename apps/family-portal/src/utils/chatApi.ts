import { ChatRequest, ChatResponse, ChatError } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://family-assistant-backend.homelab.svc.cluster.local:8001';

export class ChatApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: string
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

/**
 * Send a chat message to the backend API
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData: ChatError = await response.json().catch(() => ({
        error: 'Request failed',
        details: `HTTP ${response.status}: ${response.statusText}`,
      }));

      throw new ChatApiError(
        errorData.error || 'Request failed',
        response.status,
        errorData.details
      );
    }

    const data: ChatResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ChatApiError) {
      throw error;
    }

    // Network or parsing errors
    if (error instanceof Error) {
      throw new ChatApiError(
        'Network error',
        undefined,
        error.message
      );
    }

    throw new ChatApiError('Unknown error occurred');
  }
}

/**
 * Generate a unique session ID for chat conversations
 */
export function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Get or create a session ID from localStorage
 */
export function getOrCreateSessionId(): string {
  const storageKey = 'family_chat_session_id';
  let sessionId = localStorage.getItem(storageKey);

  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(storageKey, sessionId);
  }

  return sessionId;
}

/**
 * Clear the current session (useful for starting fresh)
 */
export function clearSession(): void {
  localStorage.removeItem('family_chat_session_id');
}
