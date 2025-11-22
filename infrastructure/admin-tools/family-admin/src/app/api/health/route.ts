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
 *   uptime: 123456,
 *   services: {
 *     familyApi: { healthy: true, message: "..." },
 *     llamacppApi: { healthy: true, message: "..." }
 *   }
 * }
 *
 * Agent Note: This endpoint checks connectivity to backend services
 * If a service is unhealthy, the app still returns 200 (it's alive)
 * Use /api/ready for readiness checks that fail if backends are down
 */

import { NextResponse } from 'next/server';
import { API_CONFIG, checkServiceHealth } from '@/lib/api-helpers';

export const dynamic = 'force-dynamic'; // Don't cache this endpoint

export async function GET() {
  const startTime = Date.now();

  // Check backend service health (non-blocking)
  const [familyApiHealth, llamacppApiHealth] = await Promise.allSettled([
    checkServiceHealth(API_CONFIG.familyApi, 'Family Assistant API'),
    checkServiceHealth(API_CONFIG.llamacppApi, 'Llama.cpp API'),
  ]);

  const responseTime = Date.now() - startTime;

  return NextResponse.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    responseTime: `${responseTime}ms`,
    services: {
      familyApi: familyApiHealth.status === 'fulfilled'
        ? familyApiHealth.value
        : { healthy: false, message: 'Health check failed' },
      llamacppApi: llamacppApiHealth.status === 'fulfilled'
        ? llamacppApiHealth.value
        : { healthy: false, message: 'Health check failed' },
    },
    environment: process.env.NODE_ENV,
  });
}
