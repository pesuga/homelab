/**
 * Server-side proxy for Phase 2 prompts/core endpoint
 * Prevents mixed content errors by keeping HTTP requests server-side
 */

import { NextResponse } from 'next/server';

const FAMILY_API_URL = process.env.FAMILY_API_URL || 'http://family-assistant-backend.homelab.svc:8001';

export async function GET() {
  try {
    const response = await fetch(`${FAMILY_API_URL}/api/phase2/prompts/core`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.status}`, details: error },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Transform single prompt response to list format
    // Backend returns: { prompt: string, length: number, estimated_tokens: number }
    // Frontend expects: { prompts: CorePromptMetadata[], total_count: number }
    if (data.prompt && !data.prompts) {
      // Create metadata for the actual core prompts
      const transformedData = {
        prompts: [
          {
            name: 'FAMILY_ASSISTANT',
            display_name: 'Family Assistant',
            description: 'Core system prompt defining the AI assistant\'s role and capabilities',
            file_path: '/prompts/core/FAMILY_ASSISTANT.md',
            version_count: 0,
            last_modified: new Date().toISOString(),
            size_bytes: data.length || 0,
            token_estimate: data.estimated_tokens || 0,
          },
          {
            name: 'PRINCIPLES',
            display_name: 'Principles',
            description: 'Guiding principles and behavioral rules for the AI assistant',
            file_path: '/prompts/core/PRINCIPLES.md',
            version_count: 0,
            last_modified: new Date().toISOString(),
            size_bytes: 0,
            token_estimate: 0,
          },
          {
            name: 'RULES',
            display_name: 'Rules',
            description: 'Specific rules and constraints for the AI assistant behavior',
            file_path: '/prompts/core/RULES.md',
            version_count: 0,
            last_modified: new Date().toISOString(),
            size_bytes: 0,
            token_estimate: 0,
          },
        ],
        total_count: 3,
      };
      return NextResponse.json(transformedData);
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to Phase 2 prompts/core endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
