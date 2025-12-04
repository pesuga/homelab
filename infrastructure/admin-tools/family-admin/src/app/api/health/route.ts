/**
 * Health Check Endpoint
 *
 * Used by Kubernetes liveness probes to determine if the application is running
 * Returns 200 if the Next.js app is responding to requests
 *
 * Path: GET /api/health
 *
 * Response:
 * {
 *   status: "ok",
 *   timestamp: "2025-01-15T10:30:00.000Z",
 *   uptime: 123456
 * }
 *
 * Agent Note: This endpoint only checks if the frontend is alive
 * It no longer checks backend services since we use direct API calls
 * Use /api/ready for readiness checks if needed
 */

import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Don't cache this endpoint

export async function GET() {
  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    message: 'Family Admin frontend is running'
  });
}