/**
 * Server-side proxy for Phase 2 health endpoint
 * Prevents mixed content errors by keeping HTTP requests server-side
 * Transforms backend response to match frontend expectations
 */

import { NextResponse } from 'next/server';

const FAMILY_API_URL = process.env.FAMILY_API_URL || 'http://family-assistant-backend.homelab.svc:8001';

export async function GET() {
  try {
    const response = await fetch(`${FAMILY_API_URL}/api/phase2/health`, {
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

    // Transform backend response to match frontend Phase2Health interface
    const transformed = {
      status: data.status || 'unknown',
      redis: {
        connected: data.layers?.redis?.status === 'healthy',
        latency_ms: data.layers?.redis?.latency_ms || 0
      },
      mem0: {
        connected: data.layers?.mem0?.status === 'healthy',
        status: data.layers?.mem0?.status || 'unknown'
      },
      qdrant: {
        connected: data.layers?.qdrant?.status === 'healthy',
        collections: data.layers?.qdrant?.collections || 0
      },
      ollama: {
        connected: data.layers?.ollama?.status === 'healthy' || false,
        models: data.layers?.ollama?.models || []
      },
      timestamp: data.timestamp
    };

    return NextResponse.json(transformed);
  } catch (error) {
    console.error('Error proxying to Phase 2 health endpoint:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
