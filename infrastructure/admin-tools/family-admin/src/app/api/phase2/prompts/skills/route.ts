import { NextRequest, NextResponse } from 'next/server';

export async function GET() {
  try {
    // Determine backend URL based on environment
    let backendUrl: string;

    if (process.env.NODE_ENV === 'production') {
      // Production: Use Kubernetes service name
      backendUrl = 'http://family-assistant-backend.homelab.svc.cluster.local:8001/api/phase2/prompts/skills';
    } else {
      // Development: Use environment variable or default to localhost
      backendUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/phase2/prompts/skills`;
    }

    console.log('Proxying skills request to:', backendUrl);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying skills request:', error);
    return NextResponse.json(
      { error: 'Failed to fetch skills from backend', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}