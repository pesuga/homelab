/**
 * API Helper Functions
 *
 * Shared utilities for Next.js API routes to handle common patterns:
 * - Error handling and transformation
 * - Request validation
 * - Response formatting
 * - Backend service proxying
 *
 * Agent Note: Import these helpers in all route.ts files for consistency
 */

import { NextResponse } from 'next/server';

/**
 * Standard API error response format
 * Ensures consistent error handling across all endpoints
 */
export interface ApiError {
  error: string;          // Human-readable error message
  code?: string;          // Machine-readable error code
  statusCode: number;     // HTTP status code
  details?: any;          // Optional additional context
}

/**
 * Environment configuration for backend services
 * These are internal Kubernetes service URLs not accessible from browser
 */
export const API_CONFIG = {
  familyApi: process.env.FAMILY_API_URL || 'https://admin.fa.pesulabs.net/api',
  llamacppApi: process.env.LLAMACPP_API_URL || 'https://admin.fa.pesulabs.net/api/llm',
  mem0Api: process.env.MEM0_API_URL || 'https://admin.fa.pesulabs.net/api/mem0',
};

/**
 * Handle API errors with consistent formatting
 *
 * @param error - Error object from try/catch
 * @param context - Additional context for debugging
 * @returns NextResponse with formatted error
 *
 * @example
 * try {
 *   const response = await fetch(url);
 * } catch (error) {
 *   return handleApiError(error, 'Failed to fetch data');
 * }
 */
export function handleApiError(error: unknown, context?: string): NextResponse {
  console.error('[API Error]', context || 'Unknown context', error);

  // Handle fetch/network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return NextResponse.json(
      {
        error: 'Failed to connect to backend service',
        code: 'BACKEND_UNREACHABLE',
        statusCode: 503,
        details: context,
      } as ApiError,
      { status: 503 }
    );
  }

  // Handle known error objects
  if (error instanceof Error) {
    return NextResponse.json(
      {
        error: error.message,
        code: 'INTERNAL_ERROR',
        statusCode: 500,
        details: context,
      } as ApiError,
      { status: 500 }
    );
  }

  // Handle unknown errors
  return NextResponse.json(
    {
      error: 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
      statusCode: 500,
      details: context,
    } as ApiError,
    { status: 500 }
  );
}

/**
 * Proxy request to backend service
 *
 * Forwards request to internal Kubernetes service and returns response
 * Handles errors, timeouts, and response transformation
 *
 * @param backendUrl - Full URL to backend service endpoint
 * @param options - Fetch options (method, headers, body, etc.)
 * @param timeout - Request timeout in milliseconds (default: 30000)
 * @returns NextResponse with backend response or error
 *
 * @example
 * return proxyToBackend(
 *   `${API_CONFIG.familyApi}/chat`,
 *   {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify(data)
 *   }
 * );
 */
export async function proxyToBackend(
  backendUrl: string,
  options: RequestInit = {},
  timeout: number = 30000
): Promise<NextResponse> {
  try {
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // Make request to backend
    const response = await fetch(backendUrl, {
      ...options,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Get response body
    const contentType = response.headers.get('content-type');
    let data: any;

    if (contentType?.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    // Return response with same status code
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': contentType || 'application/json',
      },
    });
  } catch (error) {
    // Handle abort (timeout)
    if ((error as Error).name === 'AbortError') {
      return NextResponse.json(
        {
          error: 'Request timeout',
          code: 'TIMEOUT',
          statusCode: 504,
          details: `Request to ${backendUrl} timed out after ${timeout}ms`,
        } as ApiError,
        { status: 504 }
      );
    }

    return handleApiError(error, `Proxy to ${backendUrl}`);
  }
}

/**
 * Validate required fields in request body
 *
 * @param body - Parsed request body
 * @param requiredFields - Array of required field names
 * @returns Object with validation result and error response if invalid
 *
 * @example
 * const validation = validateRequestBody(body, ['message', 'userId']);
 * if (!validation.valid) return validation.error;
 */
export function validateRequestBody(
  body: any,
  requiredFields: string[]
): { valid: boolean; error?: NextResponse } {
  if (!body || typeof body !== 'object') {
    return {
      valid: false,
      error: NextResponse.json(
        {
          error: 'Invalid request body',
          code: 'INVALID_BODY',
          statusCode: 400,
        } as ApiError,
        { status: 400 }
      ),
    };
  }

  const missingFields = requiredFields.filter(field => !(field in body));

  if (missingFields.length > 0) {
    return {
      valid: false,
      error: NextResponse.json(
        {
          error: `Missing required fields: ${missingFields.join(', ')}`,
          code: 'MISSING_FIELDS',
          statusCode: 400,
          details: { missingFields },
        } as ApiError,
        { status: 400 }
      ),
    };
  }

  return { valid: true };
}

/**
 * Get backend service health status
 *
 * @param serviceUrl - Base URL of service to check
 * @param serviceName - Human-readable service name
 * @returns Health status object
 */
export async function checkServiceHealth(
  serviceUrl: string,
  serviceName: string
): Promise<{ healthy: boolean; message: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${serviceUrl}/health`, {
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      return { healthy: true, message: `${serviceName} is healthy` };
    } else {
      return { healthy: false, message: `${serviceName} returned status ${response.status}` };
    }
  } catch (error) {
    return { healthy: false, message: `${serviceName} is unreachable` };
  }
}

/**
 * Parse JSON request body with error handling
 *
 * @param request - Next.js request object
 * @returns Parsed body or null with error response
 */
export async function parseRequestBody(
  request: Request
): Promise<{ data: any; error?: NextResponse }> {
  try {
    const body = await request.json();
    return { data: body };
  } catch (error) {
    return {
      data: null,
      error: NextResponse.json(
        {
          error: 'Invalid JSON in request body',
          code: 'INVALID_JSON',
          statusCode: 400,
        } as ApiError,
        { status: 400 }
      ),
    };
  }
}

/**
 * Extract and forward headers from client request to backend
 * Filters out headers that shouldn't be forwarded
 *
 * @param request - Next.js request object
 * @returns Headers object for backend request
 */
export function forwardHeaders(request: Request): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Forward authentication header if present
  const auth = request.headers.get('authorization');
  if (auth) {
    headers['Authorization'] = auth;
  }

  // Forward custom headers
  const customHeaders = [
    'x-request-id',
    'x-correlation-id',
    'x-user-id',
  ];

  customHeaders.forEach(header => {
    const value = request.headers.get(header);
    if (value) {
      headers[header] = value;
    }
  });

  return headers;
}
