/**
 * Server-side proxy for Phase 2 core prompts rollback endpoint
 * Handles POST for rolling back to previous versions
 */

import { NextResponse } from 'next/server';

const FAMILY_API_URL = process.env.FAMILY_API_URL || 'http://family-assistant-backend.homelab.svc:8001';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params;
    const body = await request.json();

    const response = await fetch(`${FAMILY_API_URL}/api/phase2/prompts/core/${name}/rollback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
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
    console.error('Error proxying to Phase 2 core prompt rollback endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
