/**
 * Family Members Management Endpoint
 *
 * CRUD operations for family member profiles
 * Proxies requests to family-assistant backend
 *
 * Paths:
 * - GET /api/family/members - List all family members
 * - POST /api/family/members - Create new family member
 * - PUT /api/family/members/:id - Update family member (via query param)
 * - DELETE /api/family/members/:id - Delete family member (via query param)
 *
 * GET Response:
 * {
 *   members: [
 *     {
 *       id: string,
 *       name: string,
 *       role: "parent" | "child" | "teen" | "grandparent",
 *       age?: number,
 *       preferences?: object,
 *       created_at: string,
 *       updated_at: string
 *     }
 *   ]
 * }
 *
 * POST Request:
 * {
 *   name: string,              // Required
 *   role: string,              // Required: parent/child/teen/grandparent
 *   age?: number,
 *   preferences?: object
 * }
 *
 * Agent Note: Backend stores family member data in database
 * Backend URL: http://family-assistant-backend.homelab:8001/api/family/members
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  API_CONFIG,
  handleApiError,
  parseRequestBody,
  validateRequestBody,
  proxyToBackend,
  forwardHeaders,
} from '@/lib/api-helpers';

export const dynamic = 'force-dynamic';

/**
 * GET /api/family/members
 * List all family members
 */
export async function GET(request: NextRequest) {
  try {
    const backendUrl = `${API_CONFIG.familyApi}/api/family/members`;
    const headers = forwardHeaders(request);

    return await proxyToBackend(backendUrl, {
      method: 'GET',
      headers,
    });
  } catch (error) {
    return handleApiError(error, 'GET /api/family/members');
  }
}

/**
 * POST /api/family/members
 * Create new family member
 */
export async function POST(request: NextRequest) {
  try {
    // Parse and validate request
    const { data: body, error } = await parseRequestBody(request);
    if (error) return error;

    const validation = validateRequestBody(body, ['name', 'role']);
    if (!validation.valid) return validation.error;

    // Validate role
    const validRoles = ['parent', 'child', 'teen', 'grandparent'];
    if (!validRoles.includes(body.role)) {
      return NextResponse.json(
        {
          error: `Invalid role. Must be one of: ${validRoles.join(', ')}`,
          code: 'INVALID_ROLE',
          statusCode: 400,
        },
        { status: 400 }
      );
    }

    // Proxy to backend
    const backendUrl = `${API_CONFIG.familyApi}/api/family/members`;
    const headers = forwardHeaders(request);

    return await proxyToBackend(backendUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
  } catch (error) {
    return handleApiError(error, 'POST /api/family/members');
  }
}

/**
 * PUT /api/family/members?id=xxx
 * Update existing family member
 */
export async function PUT(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const memberId = searchParams.get('id');

    if (!memberId) {
      return NextResponse.json(
        {
          error: 'Member ID is required',
          code: 'MISSING_MEMBER_ID',
          statusCode: 400,
        },
        { status: 400 }
      );
    }

    // Parse request body
    const { data: body, error } = await parseRequestBody(request);
    if (error) return error;

    // Proxy to backend
    const backendUrl = `${API_CONFIG.familyApi}/api/family/members/${memberId}`;
    const headers = forwardHeaders(request);

    return await proxyToBackend(backendUrl, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });
  } catch (error) {
    return handleApiError(error, 'PUT /api/family/members');
  }
}

/**
 * DELETE /api/family/members?id=xxx
 * Delete family member
 */
export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const memberId = searchParams.get('id');

    if (!memberId) {
      return NextResponse.json(
        {
          error: 'Member ID is required',
          code: 'MISSING_MEMBER_ID',
          statusCode: 400,
        },
        { status: 400 }
      );
    }

    // Proxy to backend
    const backendUrl = `${API_CONFIG.familyApi}/api/family/members/${memberId}`;
    const headers = forwardHeaders(request);

    return await proxyToBackend(backendUrl, {
      method: 'DELETE',
      headers,
    });
  } catch (error) {
    return handleApiError(error, 'DELETE /api/family/members');
  }
}
