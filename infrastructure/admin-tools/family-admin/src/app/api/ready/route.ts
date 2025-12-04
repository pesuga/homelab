/**
 * Readiness Check Endpoint
 *
 * Used by Kubernetes readiness probes to determine if the app is ready to serve traffic
 * Returns 200 if the frontend application is fully initialized
 *
 * Path: GET /api/ready
 *
 * Success Response (200):
 * {
 *   status: "ready",
 *   timestamp: "2025-01-15T10:30:00.000Z",
 *   message: "Frontend is ready to serve traffic"
 * }
 *
 * Agent Note: This endpoint only checks if the frontend is ready
 * Backend connectivity is handled by browser API calls directly
 * If critical services are down, the browser will show appropriate errors
 */

import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Don't cache this endpoint

export async function GET() {
  // In Next.js, the app is considered ready once it's built and running
  // We don't need to check backend services since browser handles direct API calls
  const isReady = true;

  const response = {
    status: isReady ? 'ready' : 'not_ready',
    timestamp: new Date().toISOString(),
    message: 'Frontend is ready to serve traffic',
  };

  return NextResponse.json(response, {
    status: isReady ? 200 : 503,
  });
}