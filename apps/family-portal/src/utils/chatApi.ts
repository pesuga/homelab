import { ChatRequest, ChatResponse, ChatError } from '../types/chat';

// Use relative path to proxy through nginx (avoids mixed content and CORS)
// Frontend is served via HTTPS, backend is accessed via same origin
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

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
 * Send a chat message to the backend API using OpenAI-compatible endpoint
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  try {
    // Use OpenAI-compatible endpoint which doesn't require authentication
    const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'user',
            content: request.message
          }
        ],
        user: request.user_id || 'guest',
        stream: false
      }),
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

    const data = await response.json();

    // Convert OpenAI response format to our ChatResponse format
    return {
      response: data.choices[0].message.content,
      session_id: request.session_id || '',
      metadata: data.metadata
    };
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
