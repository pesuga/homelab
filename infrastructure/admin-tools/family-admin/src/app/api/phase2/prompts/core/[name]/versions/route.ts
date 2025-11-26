/**
 * Server-side proxy for Phase 2 core prompts versions endpoint
 * Handles GET for version history of core prompts
 */

import { NextResponse } from 'next/server';

const FAMILY_API_URL = process.env.FAMILY_API_URL || 'http://family-assistant-backend.homelab.svc:8001';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params;

    // Check if this is requesting a specific version (timestamp in URL path)
    // Example: /api/phase2/prompts/core/FAMILY_ASSISTANT/versions/2025-11-26T10-30-00Z
    const url = new URL(request.url);
    const pathParts = url.pathname.split('/');
    const versionsIndex = pathParts.indexOf('versions');
    const timestamp = pathParts[versionsIndex + 1];

    let apiUrl = `${FAMILY_API_URL}/api/phase2/prompts/core/${name}/versions`;
    if (timestamp) {
      apiUrl = `${FAMILY_API_URL}/api/phase2/prompts/core/${name}/versions/${timestamp}`;
    }

    const response = await fetch(apiUrl, {
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
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to Phase 2 core prompt versions endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
