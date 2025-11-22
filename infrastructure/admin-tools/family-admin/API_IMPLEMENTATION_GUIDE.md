# Family Admin API Implementation Guide

## Overview

This document explains the API route architecture for the Family Admin panel. The API routes solve the fundamental problem of browser clients being unable to access internal Kubernetes services.

## The Problem

**Before API Routes:**
```
Browser → http://family-assistant-backend.homelab:8001 ❌
(Browser cannot resolve *.svc.cluster.local DNS)
```

**With API Routes:**
```
Browser → /api/family/chat (same-origin)
         → Next.js API Route (server-side)
         → http://family-assistant-backend.homelab:8001 ✅
```

## Architecture

### Component Layers

1. **Browser (Client-Side)**
   - React components
   - Only accesses `/api/*` routes
   - No direct backend access

2. **Next.js API Routes (Server-Side)**
   - Runs in Node.js server
   - Can access internal Kubernetes services
   - Proxies requests/responses
   - Located in: `src/app/api/`

3. **Backend Services (Internal)**
   - family-assistant-backend
   - llamacpp LLM service
   - mem0 memory service
   - Only accessible from within cluster

### File Structure

```
src/app/api/
├── README.md                    # API routes overview
├── health/
│   └── route.ts                # GET /api/health
├── ready/
│   └── route.ts                # GET /api/ready
├── family/
│   ├── chat/
│   │   └── route.ts            # POST /api/family/chat
│   ├── members/
│   │   └── route.ts            # GET/POST/PUT/DELETE /api/family/members
│   └── [...path]/
│       └── route.ts            # Catch-all proxy for /api/family/*
└── llm/
    └── chat/
        └── route.ts            # POST /api/llm/chat

src/lib/
└── api-helpers.ts              # Shared utilities for API routes
```

## Environment Variables

### Server-Side Only (API Routes)

These are used by API routes and NOT exposed to browser:

```bash
FAMILY_API_URL=http://family-assistant-backend.homelab:8001
LLAMACPP_API_URL=http://llamacpp-kimi-vl-service.llamacpp:8080
MEM0_API_URL=http://mem0.homelab:8080
```

### Client-Side (Browser)

These are embedded in browser JavaScript (prefix with `NEXT_PUBLIC_`):

```bash
NEXT_PUBLIC_APP_URL=https://app.fa.pesulabs.net
```

## API Route Examples

### Health Check

```typescript
// src/app/api/health/route.ts
import { NextResponse } from 'next/server';
import { checkServiceHealth, API_CONFIG } from '@/lib/api-helpers';

export async function GET() {
  const health = await checkServiceHealth(
    API_CONFIG.familyApi,
    'Family API'
  );

  return NextResponse.json({
    status: 'ok',
    services: { familyApi: health }
  });
}
```

**Usage:**
```bash
curl http://localhost:3000/api/health
```

### Chat Proxy

```typescript
// src/app/api/family/chat/route.ts
export async function POST(request: NextRequest) {
  const { data: body } = await parseRequestBody(request);

  return await proxyToBackend(
    `${API_CONFIG.familyApi}/api/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    }
  );
}
```

**Usage:**
```typescript
// In React component
const response = await fetch('/api/family/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello' })
});
```

## Helper Functions

### `proxyToBackend()`

Proxies request to internal service with timeout and error handling.

```typescript
await proxyToBackend(
  `${API_CONFIG.familyApi}/endpoint`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  },
  30000 // 30s timeout
);
```

### `handleApiError()`

Consistent error formatting across all endpoints.

```typescript
try {
  // ... API logic
} catch (error) {
  return handleApiError(error, 'Context for debugging');
}
```

**Error Response Format:**
```json
{
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "statusCode": 500,
  "details": "Additional context"
}
```

### `validateRequestBody()`

Validates required fields in request.

```typescript
const validation = validateRequestBody(body, ['message', 'userId']);
if (!validation.valid) return validation.error;
```

## Usage Patterns

### 1. Simple Proxy

For straightforward pass-through to backend:

```typescript
export async function GET(request: NextRequest) {
  return await proxyToBackend(
    `${API_CONFIG.familyApi}/api/data`,
    { method: 'GET', headers: forwardHeaders(request) }
  );
}
```

### 2. Validation + Proxy

For endpoints requiring input validation:

```typescript
export async function POST(request: NextRequest) {
  // Parse body
  const { data: body, error } = await parseRequestBody(request);
  if (error) return error;

  // Validate
  const validation = validateRequestBody(body, ['required_field']);
  if (!validation.valid) return validation.error;

  // Proxy
  return await proxyToBackend(
    `${API_CONFIG.familyApi}/api/endpoint`,
    {
      method: 'POST',
      headers: forwardHeaders(request),
      body: JSON.stringify(body)
    }
  );
}
```

### 3. Transform Response

For endpoints that need to transform backend response:

```typescript
export async function GET(request: NextRequest) {
  const response = await fetch(`${API_CONFIG.familyApi}/api/data`);
  const data = await response.json();

  // Transform data
  const transformed = {
    ...data,
    timestamp: new Date().toISOString(),
    formatted: data.raw.map(item => ({ id: item.id, name: item.name }))
  };

  return NextResponse.json(transformed);
}
```

## Testing

### Local Development

1. **Setup environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with local service URLs
   ```

2. **Start dev server:**
   ```bash
   npm run dev
   ```

3. **Test health endpoint:**
   ```bash
   curl http://localhost:3000/api/health
   ```

4. **Test chat endpoint:**
   ```bash
   curl -X POST http://localhost:3000/api/family/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello"}'
   ```

### Production Testing

```bash
# Health check
curl https://admin.fa.pesulabs.net/api/health

# Chat endpoint
curl -X POST https://admin.fa.pesulabs.net/api/family/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

## Common Patterns for AI Agents

### Adding a New Endpoint

1. **Create route file:**
   ```bash
   # For: POST /api/family/tasks
   # Create: src/app/api/family/tasks/route.ts
   ```

2. **Implement handler:**
   ```typescript
   import { NextRequest } from 'next/server';
   import { API_CONFIG, proxyToBackend, parseRequestBody, handleApiError } from '@/lib/api-helpers';

   export async function POST(request: NextRequest) {
     try {
       const { data: body, error } = await parseRequestBody(request);
       if (error) return error;

       return await proxyToBackend(
         `${API_CONFIG.familyApi}/api/tasks`,
         {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(body)
         }
       );
     } catch (error) {
       return handleApiError(error, 'POST /api/family/tasks');
     }
   }
   ```

3. **Add documentation comment:**
   ```typescript
   /**
    * Family Tasks Endpoint
    *
    * Create and manage family tasks
    *
    * Path: POST /api/family/tasks
    *
    * Request: { title: string, assignedTo: string, dueDate: string }
    * Response: { id: string, created: boolean }
    */
   ```

### Updating Environment Variables

1. **Add to `.env.example`:**
   ```bash
   NEW_SERVICE_URL=http://new-service.homelab:8080
   ```

2. **Add to `api-helpers.ts`:**
   ```typescript
   export const API_CONFIG = {
     // ... existing
     newService: process.env.NEW_SERVICE_URL || 'http://default:8080',
   };
   ```

3. **Update Kubernetes deployment:**
   ```yaml
   env:
   - name: NEW_SERVICE_URL
     value: "http://new-service.homelab.svc.cluster.local:8080"
   ```

## Security Considerations

1. **CORS:** Not needed - same-origin requests
2. **Authentication:** Add to `forwardHeaders()` if needed
3. **Rate Limiting:** Implement in Kubernetes ingress or middleware
4. **Input Validation:** Always validate request bodies
5. **Error Messages:** Don't expose internal details in production

## Troubleshooting

### Issue: "Failed to connect to backend service"

**Cause:** Backend service unreachable from Next.js pod

**Solution:**
```bash
# Check if service exists
kubectl get svc family-assistant-backend -n homelab

# Test from pod
kubectl exec -it family-admin-xxx -n homelab -- \
  curl http://family-assistant-backend.homelab:8001/health
```

### Issue: "NEXT_PUBLIC_API_URL not defined"

**Cause:** Still using old client-side environment variable

**Solution:** Remove `NEXT_PUBLIC_API_URL` and use API routes instead:
```typescript
// ❌ Old way
const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/chat');

// ✅ New way
const response = await fetch('/api/family/chat');
```

### Issue: API route returns 404

**Cause:** Route file in wrong location or not exported properly

**Solution:**
1. Verify file is at `src/app/api/[path]/route.ts`
2. Ensure function is exported: `export async function GET() { }`
3. Check Next.js dev server logs for route registration

## Performance Optimization

1. **Caching:** Add `export const revalidate = 60` for static data
2. **Timeout:** Adjust timeout based on endpoint needs
3. **Parallel Requests:** Use `Promise.allSettled()` for multiple backends
4. **Streaming:** For large responses, consider streaming

## References

- [Next.js Route Handlers](https://nextjs.org/docs/app/building-your-application/routing/route-handlers)
- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- [Kubernetes Service DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
