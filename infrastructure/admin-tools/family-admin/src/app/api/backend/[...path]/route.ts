/**
 * Backend API Proxy
 *
 * Forwards requests from /api/backend/* to the Family Assistant Backend API
 * This avoids CORS issues and SSL certificate problems by proxying through Next.js
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.FAMILY_API_URL || 'http://family-assistant-api.fa-platform.svc.cluster.local:8001';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path, 'PATCH');
}

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  try {
    // Reconstruct the path
    const path = pathSegments.join('/');

    // Get query parameters
    const searchParams = request.nextUrl.searchParams.toString();
    const queryString = searchParams ? `?${searchParams}` : '';

    // Build backend URL
    const backendUrl = `${BACKEND_URL}/${path}${queryString}`;

    console.log(`[Backend Proxy] ${method} ${backendUrl}`);

    // Prepare headers (forward relevant headers, exclude host)
    const headers: Record<string, string> = {};
    request.headers.forEach((value, key) => {
      if (!['host', 'connection'].includes(key.toLowerCase())) {
        headers[key] = value;
      }
    });

    // DEVELOPMENT MODE: If no Authorization header is present, add legacy headers for development
    // This allows the admin interface to work without full Authentik OIDC integration
    if (!headers['authorization'] && !headers['Authorization']) {
      // Use legacy X-User-Id header with demo admin ID
      headers['X-User-Id'] = 'a0000000-0000-0000-0000-000000000001';
      console.log('[Backend Proxy] No auth header found, using development mode with legacy X-User-Id');
    }

    // Prepare request options
    const options: RequestInit = {
      method,
      headers,
    };

    // Add body for methods that support it
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      const body = await request.text();
      if (body) {
        options.body = body;
      }
    }

    // Make request to backend
    const response = await fetch(backendUrl, options);

    // Get response body
    const responseBody = await response.text();

    // Forward response
    return new NextResponse(responseBody, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'application/json',
      },
    });
  } catch (error) {
    console.error('[Backend Proxy] Error:', error);
    return NextResponse.json(
      { error: 'Backend proxy error', details: String(error) },
      { status: 500 }
    );
  }
}
