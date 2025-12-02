/**
 * Family Assistant Chat Endpoint
 *
 * Proxies chat requests from browser to family-assistant backend
 * Handles message streaming and response formatting
 *
 * Path: POST /api/family/chat
 *
 * Request Body:
 * {
 *   message: string,           // User's chat message
 *   userId?: string,           // Optional user ID for context
 *   sessionId?: string,        // Optional session ID for conversation continuity
 *   stream?: boolean,          // Optional streaming mode (default: false)
 * }
 *
 * Response:
 * {
 *   response: string,          // AI assistant response
 *   sessionId: string,         // Session ID for follow-up messages
 *   timestamp: string,         // ISO timestamp
 *   model?: string,           // Model used for response
 *   usage?: {                 // Optional token usage stats
 *     promptTokens: number,
 *     completionTokens: number,
 *     totalTokens: number
 *   }
 * }
 *
 * Agent Note: This is the primary chat interface endpoint
 * Backend URL: http://family-assistant-backend.homelab:8001/api/chat
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  API_CONFIG,
  handleApiError,
  parseRequestBody,
  validateRequestBody,
  proxyToBackend,
  forwardHeaders,
} from '@/lib/api-helpers';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const { data: body, error } = await parseRequestBody(request);
    if (error) return error;

    // Validate required fields
    const validation = validateRequestBody(body, ['message']);
    if (!validation.valid) return validation.error;

    // Prepare backend request
    const backendUrl = `${API_CONFIG.familyApi}/api/chat`;
    const headers = forwardHeaders(request);

    // Proxy to backend
    return await proxyToBackend(
      backendUrl,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: body.message,
          user_id: body.userId,
          session_id: body.sessionId,
          stream: body.stream || false,
        }),
      },
      30000 // 30 second timeout for chat
    );
  } catch (error) {
    return handleApiError(error, 'Chat endpoint');
  }
}
