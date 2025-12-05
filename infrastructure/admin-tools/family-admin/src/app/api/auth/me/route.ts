/**
 * Authentication API Endpoint
 *
 * Reads Authentik headers from the request and returns user profile.
 * This endpoint works with Authentik ForwardAuth middleware.
 *
 * Headers expected from Authentik:
 * - X-authentik-username: Username
 * - X-authentik-email: Email address
 * - X-authentik-name: Full name
 * - X-authentik-groups: Comma-separated groups
 * - X-authentik-uid: User UUID
 */

import { NextResponse } from 'next/server';
import { extractUserFromHeaders, getUserProfile } from '@/lib/authentik';

export const dynamic = 'force-dynamic'; // Don't cache this endpoint

export async function GET(request: Request) {
  try {
    // Extract user from Authentik headers
    const user = extractUserFromHeaders(request.headers);

    if (!user) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      );
    }

    // Return user profile in the expected format
    const profile = getUserProfile(user);

    return NextResponse.json(profile);
  } catch (error) {
    console.error('Auth endpoint error:', error);
    return NextResponse.json(
      { error: 'Authentication check failed' },
      { status: 500 }
    );
  }
}