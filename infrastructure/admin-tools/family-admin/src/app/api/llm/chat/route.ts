/**
 * LLM Chat Endpoint
 *
 * Direct access to llama.cpp Kimi-VL model for chat completions
 * Bypasses family-assistant backend for raw LLM access
 *
 * Path: POST /api/llm/chat
 *
 * Request Body:
 * {
 *   message: string,           // User message
 *   temperature?: number,      // 0.0 - 2.0 (default: 0.7)
 *   max_tokens?: number,       // Max response length (default: 512)
 *   system_prompt?: string,    // Optional system message
 *   conversation_history?: Array<{role: string, content: string}>
 * }
 *
 * Response:
 * {
 *   response: string,          // AI response
 *   model: string,             // Model name
 *   usage: {
 *     prompt_tokens: number,
 *     completion_tokens: number,
 *     total_tokens: number
 *   },
 *   finish_reason: string
 * }
 *
 * Agent Note: This endpoint directly accesses llama.cpp server
 * Backend URL: http://llamacpp-kimi-vl-service.llamacpp:8080/v1/chat/completions
 * Model: Kimi-VL-A3B-Thinking-2506 (8K context window)
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  API_CONFIG,
  handleApiError,
  parseRequestBody,
  validateRequestBody,
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

    // Prepare messages array for OpenAI-compatible API
    const messages: Array<{ role: string; content: string }> = [];

    // Add system prompt if provided
    if (body.system_prompt) {
      messages.push({
        role: 'system',
        content: body.system_prompt,
      });
    }

    // Add conversation history if provided
    if (body.conversation_history && Array.isArray(body.conversation_history)) {
      messages.push(...body.conversation_history);
    }

    // Add current user message
    messages.push({
      role: 'user',
      content: body.message,
    });

    // Call llama.cpp API
    const llamacppUrl = `${API_CONFIG.llamacppApi}/v1/chat/completions`;

    const response = await fetch(llamacppUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'kimi-vl',
        messages,
        temperature: body.temperature || 0.7,
        max_tokens: body.max_tokens || 512,
        stream: false,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        {
          error: 'LLM service error',
          code: 'LLM_ERROR',
          statusCode: response.status,
          details: errorText,
        },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Extract and format response
    return NextResponse.json({
      response: data.choices[0]?.message?.content || '',
      model: data.model,
      usage: {
        prompt_tokens: data.usage?.prompt_tokens || 0,
        completion_tokens: data.usage?.completion_tokens || 0,
        total_tokens: data.usage?.total_tokens || 0,
      },
      finish_reason: data.choices[0]?.finish_reason || 'stop',
    });
  } catch (error) {
    return handleApiError(error, 'LLM chat endpoint');
  }
}
