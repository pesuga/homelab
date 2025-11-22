/**
 * Catch-All Family API Proxy
 *
 * Proxies any unmatched /api/family/* requests to the backend
 * Allows frontend to access any backend endpoint without creating individual routes
 *
 * Path: /api/family/[...anything]
 *
 * Examples:
 * - GET /api/family/settings → http://family-backend:8001/api/family/settings
 * - POST /api/family/calendar → http://family-backend:8001/api/family/calendar
 * - GET /api/family/notifications/unread → http://family-backend:8001/api/family/notifications/unread
 *
 * Agent Note: This is a wildcard proxy for all family-assistant backend endpoints
 * Specific routes (like /api/family/chat) take precedence over this catch-all
 * Use this for rapid development without creating individual proxy routes
 *
 * Security Note: Ensure backend implements proper authentication/authorization
 * This route forwards all requests without additional validation
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  API_CONFIG,
  handleApiError,
  proxyToBackend,
  forwardHeaders,
} from '@/lib/api-helpers';

export const dynamic = 'force-dynamic';

/**
 * Handle all HTTP methods (GET, POST, PUT, DELETE, PATCH)
 */
async function handleRequest(request: NextRequest, method: string) {
  try {
    // Extract path segments after /api/family/
    const url = new URL(request.url);
    const pathSegments = url.pathname.split('/api/family/')[1] || '';

    // Construct backend URL
    const backendUrl = `${API_CONFIG.familyApi}/api/family/${pathSegments}${url.search}`;

    // Prepare headers
    const headers = forwardHeaders(request);

    // Get request body if present
    let body: string | undefined;
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      try {
        const requestBody = await request.json();
        body = JSON.stringify(requestBody);
      } catch (error) {
        // No body or invalid JSON, proceed without body
      }
    }

    // Proxy to backend
    return await proxyToBackend(backendUrl, {
      method,
      headers,
      body,
    });
  } catch (error) {
    return handleApiError(error, `${method} /api/family/${method}`);
  }
}

export async function GET(request: NextRequest) {
  return handleRequest(request, 'GET');
}

export async function POST(request: NextRequest) {
  return handleRequest(request, 'POST');
}

export async function PUT(request: NextRequest) {
  return handleRequest(request, 'PUT');
}

export async function DELETE(request: NextRequest) {
  return handleRequest(request, 'DELETE');
}

export async function PATCH(request: NextRequest) {
  return handleRequest(request, 'PATCH');
}
