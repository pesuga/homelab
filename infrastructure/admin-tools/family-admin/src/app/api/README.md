# Family Admin API Routes

This directory contains Next.js API routes that act as a proxy layer between the browser-based admin panel and backend services running in the Kubernetes cluster.

## Architecture

```
Browser (Client)
    ↓
Next.js API Routes (This Layer)
    ↓
Internal Kubernetes Services
    ├─ family-assistant-backend.homelab.svc.cluster.local:8001
    └─ Other internal services
```

## Why API Routes?

**Problem**: Browser clients cannot access internal Kubernetes DNS names or cluster IPs.

**Solution**: Next.js API routes run server-side and can access internal services, then proxy responses to the browser.

**Benefits**:
- ✅ Security: Backend URLs not exposed to browser
- ✅ CORS: Same-origin requests (no CORS issues)
- ✅ Authentication: Server-side token handling
- ✅ Error handling: Centralized error transformation
- ✅ Caching: Server-side response caching

## Environment Variables

These variables are used server-side only (no `NEXT_PUBLIC_` prefix):

```bash
# Backend Services (internal cluster DNS)
FAMILY_API_URL=http://family-assistant-backend.homelab.svc.cluster.local:8001
LLAMACPP_API_URL=http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080
MEM0_API_URL=http://mem0.homelab.svc.cluster.local:8080

# Authentication
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=https://admin.fa.pesulabs.net
```

## API Route Structure

```
/api/
├── health/             # Health check endpoints
│   └── route.ts        # GET /api/health
├── ready/              # Readiness check
│   └── route.ts        # GET /api/ready
├── family/             # Family Assistant backend proxy
│   ├── chat/
│   │   └── route.ts    # POST /api/family/chat
│   ├── members/
│   │   └── route.ts    # GET/POST/PUT/DELETE /api/family/members
│   └── [...path]/
│       └── route.ts    # Catch-all proxy
└── llm/                # LLM service proxy
    └── route.ts        # POST /api/llm/chat
```

## Usage Examples

### From Browser (Client-Side)

```typescript
// ✅ Correct: Use relative API routes
const response = await fetch('/api/family/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello' })
});

// ❌ Wrong: Don't use internal cluster URLs
const response = await fetch('http://family-assistant-backend.homelab:8001/chat', {
  // This will fail - browser can't resolve cluster DNS
});
```

### From Server Components

```typescript
// Can use either API routes or direct internal URLs
const apiUrl = process.env.FAMILY_API_URL;
const response = await fetch(`${apiUrl}/chat`);
```

## Error Handling

All API routes follow consistent error response format:

```typescript
{
  error: string,           // Human-readable error message
  code?: string,          // Error code for programmatic handling
  statusCode: number,     // HTTP status code
  details?: any          // Optional additional context
}
```

## Rate Limiting

API routes implement rate limiting to prevent abuse:
- Anonymous: 60 requests/minute
- Authenticated: 300 requests/minute

## Caching Strategy

- Health checks: No cache
- Static data: 5 minutes
- User data: No cache
- LLM responses: No cache

## Adding New Routes

1. Create new directory under `/api/`
2. Add `route.ts` with handlers
3. Document in this README
4. Add TypeScript types in `/types/api.ts`
5. Update environment variables if needed

## Testing

```bash
# Health check
curl http://localhost:3000/api/health

# Chat endpoint
curl -X POST http://localhost:3000/api/family/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Agent-Friendly Documentation

**For AI Agents modifying this codebase:**

1. **Pattern**: All routes follow `/api/<service>/<endpoint>` structure
2. **File location**: Each endpoint = directory with `route.ts`
3. **Error handling**: Use `handleApiError()` helper (see `/lib/api-helpers.ts`)
4. **Types**: Import from `/types/api.ts`
5. **Environment**: Server-side only, use `process.env.VARIABLE_NAME`
6. **Testing**: Always add health check and error case tests

**Common Tasks**:
- Add new endpoint: Create `src/app/api/<path>/route.ts`
- Proxy to new service: Add `SERVICE_URL` env var, create proxy route
- Update error handling: Modify `/lib/api-helpers.ts`
- Add authentication: Use middleware in route handler

**Key Files**:
- Route handlers: `src/app/api/**/route.ts`
- Shared helpers: `src/lib/api-helpers.ts`
- Type definitions: `src/types/api.ts`
- Environment config: `.env.local` (dev), k8s deployment (prod)
