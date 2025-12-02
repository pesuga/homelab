/**
 * Readiness Check Endpoint
 *
 * Used by Kubernetes readiness probes to determine if the app is ready to serve traffic
 * Returns 200 only if all critical backend services are reachable
 *
 * Path: GET /api/ready
 *
 * Success Response (200):
 * {
 *   status: "ready",
 *   timestamp: "2025-01-15T10:30:00.000Z",
 *   services: {
 *     familyApi: { healthy: true, message: "..." }
 *   }
 * }
 *
 * Error Response (503):
 * {
 *   status: "not_ready",
 *   timestamp: "2025-01-15T10:30:00.000Z",
 *   services: {
 *     familyApi: { healthy: false, message: "..." }
 *   }
 * }
 *
 * Agent Note: This endpoint MUST succeed for the pod to receive traffic
 * If critical services are down, this returns 503 and pod is removed from load balancer
 */

import { NextResponse } from 'next/server';
import { API_CONFIG, checkServiceHealth } from '@/lib/api-helpers';

export const dynamic = 'force-dynamic'; // Don't cache this endpoint

export async function GET() {
  // Check critical backend services
  const [familyApiHealth] = await Promise.allSettled([
    checkServiceHealth(API_CONFIG.familyApi, 'Family Assistant API'),
  ]);

  const familyApiResult = familyApiHealth.status === 'fulfilled'
    ? familyApiHealth.value
    : { healthy: false, message: 'Health check failed' };

  // Determine if app is ready (all critical services must be healthy)
  const isReady = familyApiResult.healthy;

  const response = {
    status: isReady ? 'ready' : 'not_ready',
    timestamp: new Date().toISOString(),
    services: {
      familyApi: familyApiResult,
    },
  };

  return NextResponse.json(response, {
    status: isReady ? 200 : 503,
  });
}
