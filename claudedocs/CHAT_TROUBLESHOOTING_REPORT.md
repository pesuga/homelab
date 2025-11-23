# Family Assistant Chat - Comprehensive Troubleshooting Report

**Date**: 2025-11-22
**Issue**: Chat returning generic error "I encountered an error while processing your request" with no console errors
**Reporter**: Frontend investigation for backend agent

---

## Executive Summary

The Family Assistant chat functionality is failing with a generic error message visible to users, but **NO errors appear in the browser console**. Backend investigation revealed the service is **running and initialized successfully**, but experiencing **connectivity failures to dependent services** (Ollama embedding service) and **validation errors** in the search/memory system.

**Critical Finding**: Backend logs show successful startup but runtime errors when processing chat requests:
1. ❌ **Embedding service connection failure**: "All connection attempts failed" to Ollama at `100.72.98.106:11434`
2. ❌ **Pydantic validation error**: `SearchRequest.filter.user_id` - "Extra inputs are not permitted"
3. ⚠️ **404 Not Found** on port 30880 (unknown service dependency)

---

## Frontend Implementation Analysis

### Chat Flow Architecture

**Frontend → Backend API Flow:**
```
User sends message in ChatInterface.tsx
    ↓
chatApi.ts makes POST to /v1/chat/completions
    ↓
API URL: ${VITE_API_BASE_URL}/v1/chat/completions
    ↓
Default: /api/v1/chat/completions (proxied through Traefik)
    ↓
Backend service: family-assistant-backend.homelab.svc.cluster.local:8001
```

### Key Frontend Files

#### 1. **Chat API Client** (`apps/family-portal/src/utils/chatApi.ts`)
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages: [{ role: 'user', content: request.message }],
      user: request.user_id || 'guest',
      stream: false
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new ChatApiError(
      errorData?.error || 'Failed to send message',
      response.status,
      errorData
    );
  }

  return response.json();
}
```

**Request Format (OpenAI-compatible)**:
```json
{
  "messages": [
    { "role": "user", "content": "<user message>" }
  ],
  "user": "<user_id or 'guest'>",
  "stream": false
}
```

**Expected Response**:
```json
{
  "id": "chatcmpl-<uuid>",
  "object": "chat.completion",
  "created": <timestamp>,
  "model": "family-assistant",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "<response text>"
      },
      "finish_reason": "stop"
    }
  ]
}
```

#### 2. **Chat Interface** (`apps/family-portal/src/components/ChatInterface.tsx`)

**Error Handling:**
```typescript
catch (error) {
  setMessages((prev) =>
    prev.map((msg) =>
      msg.id === userMessage.id ? { ...msg, status: 'error' } : msg
    )
  );

  let errorMessage = 'Failed to send message. Please try again.';
  if (error instanceof ChatApiError) {
    errorMessage = error.message;
    if (error.details) {
      console.error('Chat API Error:', error.details);  // ← Should log to console
    }
  }

  toast.error(errorMessage, { duration: 4000, icon: '⚠️' });
}
```

**Critical Observation**: The code **should** log errors to console if `error.details` exists, but user reports **no console errors**. This suggests:
- Error response doesn't include `details` field
- Error is caught before reaching this handler
- Network/CORS error preventing proper error response

#### 3. **Configuration** (`apps/family-portal/src/lib/api.ts`)
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = {
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
};
```

**Note**: `chatApi.ts` doesn't use this client - it makes direct `fetch()` calls.

---

## Backend Implementation Analysis

### Service Architecture

**Backend Stack (from deployment config)**:
- **Runtime**: FastAPI + Uvicorn on Python 3.12
- **Port**: 8001 (main API)
- **Additional Ports**: 8123, 8008 (enhancement service)
- **Database**: PostgreSQL at `postgres.homelab.svc.cluster.local:5432`
- **Cache**: Redis at `redis.homelab.svc.cluster.local:6379`
- **LLM Service**: Ollama at `http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080`
- **Memory Service**: Mem0 at `http://mem0.homelab.svc.cluster.local:8080`

### Backend Service Status

**✅ Services Successfully Initialized:**
```
✅ Structured logging configured: DEBUG
✅ OpenTelemetry tracing configured: family-assistant-api -> http://otel-collector.homelab.svc.cluster.local:4317
✅ Prometheus metrics configured: /metrics endpoint
✅ Rate limiting configured: 100/min, 1000/hour per user/IP
✅ Redis connection established
✅ Mem0 client ready
✅ Qdrant collections initialized
✅ Ollama embedding service connected
✅ Prompt templates loaded
✅ Role prompts cached
✅ Bilingual context ready
✅ Phase 2 services initialized successfully!
✅ Family Assistant API started on 0.0.0.0:8001
```

**⚠️ Startup Warning:**
```
/usr/local/lib/python3.12/site-packages/pydub/utils.py:170: RuntimeWarning:
Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work
```

### Chat Endpoint Implementation (`services/family-api/src/api/main.py:1631-1724`)

**Endpoint**: `POST /v1/chat/completions`

**Key Implementation Details**:
```python
@app.post("/v1/chat/completions", response_model=OpenAIChatResponse)
async def openai_chat_completions(request: OpenAIChatRequest):
    user_id = request.user or "default"
    user_messages = [msg for msg in request.messages if msg.role == "user"]
    last_message = user_messages[-1].content
    thread_id = f"thread_{user_id}_{uuid.uuid4().hex[:8]}"

    # Get user profile from PostgreSQL
    async with db_pool.acquire() as conn:
        user_row = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1",
            user_id
        )

        # Build user profile
        user_profile = {
            "user_id": user_id,
            "name": user_row["name"] if user_row else "Guest",
            "age_group": user_row["age_group"] if user_row else "adult",
            # ... more profile fields
        }

        # Chat with agent (LangGraph agent)
        result = await agent.chat(
            message=last_message,
            user_id=user_id,
            thread_id=thread_id,
            user_profile=user_profile
        )

    # Return OpenAI-compatible response
    return OpenAIChatResponse(...)
```

**Dependencies**:
1. PostgreSQL database connection (user profiles)
2. LangGraph agent (`agent.chat()` method)
3. Memory/embedding services (Qdrant, Ollama, Mem0)
4. Prompt system (loaded from `/app/prompts-data`)

---

## Error Analysis

### Runtime Errors from Backend Logs

#### 1. **Embedding Service Connection Failure** 🔴 CRITICAL
```json
{
  "logger": "httpcore.connection",
  "message": "connect_tcp.started host='100.72.98.106' port=11434",
  "service": "family-assistant-api"
}
{
  "logger": "httpcore.connection",
  "message": "connect_tcp.failed exception=ConnectError(OSError('All connection attempts failed'))",
  "service": "family-assistant-api"
}
```

**Error Message**: `Error generating embedding: All connection attempts failed`

**Analysis**:
- **Target**: `100.72.98.106:11434` (Ollama embedding service)
- **Failure**: TCP connection refused/timeout
- **Impact**: Cannot generate embeddings for semantic search/memory
- **Root Cause**: Either:
  - Ollama service not running on that host
  - Firewall blocking port 11434
  - Wrong IP address in configuration
  - Network routing issue

**Expected Configuration** (from deployment):
```yaml
OLLAMA_HOST: http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080
```

**Question**: Why is the backend trying to connect to `100.72.98.106:11434` instead of the Kubernetes service DNS?

#### 2. **Pydantic Validation Error** 🔴 CRITICAL
```json
{
  "logger": "api.services.llm_service",
  "message": "Error in LLM chat: 1 validation error for SearchRequest\nfilter.user_id\n  Extra inputs are not permitted [type=extra_forbidden, input_value='1', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.10/v/extra_forbidden",
  "service": "family-assistant-api"
}
```

**Analysis**:
- **Model**: `SearchRequest` (likely for Qdrant vector search)
- **Field**: `filter.user_id`
- **Error**: "Extra inputs are not permitted"
- **Value**: `'1'` (string)
- **Root Cause**: Pydantic model doesn't allow `user_id` in the `filter` field, or model configuration has `extra='forbid'`

**Impact**: Memory/search functionality fails when trying to filter by user

**Pydantic Configuration Issue**:
```python
# Current (failing):
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')  # ← Rejects extra fields
    filter: SomeFilterType  # ← Doesn't include user_id

# Needs to be either:
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra='allow')  # Option 1: Allow extra fields
    # OR
    filter: FilterType  # Option 2: FilterType explicitly includes user_id
```

#### 3. **404 Not Found on Port 30880** ⚠️ WARNING
```json
{
  "logger": "httpcore.http11",
  "message": "receive_response_headers.complete return_value=(b'HTTP/1.1', 404, b'Not Found', ...)",
  "service": "family-assistant-api"
}
```

**Analysis**:
- **Target**: `100.81.76.55:30880` (NodePort or external service)
- **Response**: HTTP 404 Not Found
- **Impact**: Unknown - depends on what this service does
- **Need**: Identify what service runs on port 30880 and why it's returning 404

---

## Network Connectivity Testing

### Direct Backend Service Test
```bash
$ kubectl exec -it -n homelab deployment/family-assistant-frontend -- \
  curl -v http://family-assistant-backend.homelab.svc.cluster.local:8001/health

# Result: Connection timeout
# Error: Failed to connect after 10241 ms: Couldn't connect to server
```

**Findings**:
- ❌ Backend service **not responding** on port 8001 from within cluster
- ✅ Backend pod is **running** (logs show successful startup)
- ⚠️ Service endpoint may be misconfigured

### Service Configuration Check
```bash
$ kubectl get svc -n homelab | grep family

family-assistant-backend      ClusterIP   10.43.116.179   <none>   8001/TCP,8123/TCP,8008/TCP
```

**Service Exists**: ✅ ClusterIP `10.43.116.179` with ports 8001, 8123, 8008

**Hypothesis**: Service selector may not match pod labels, or pod not exposing port 8001 correctly.

---

## System Dependencies

### Required Services (from requirements.txt)

**Core Framework**:
- `langgraph==0.2.56` - LangGraph agent framework
- `langchain-core==0.3.28` - LangChain core
- `langchain-ollama==0.2.2` - Ollama integration

**Memory & RAG**:
- `mem0ai==0.1.39` - Memory service
- `qdrant-client==1.12.1` - Vector database

**Database**:
- `asyncpg==0.30.0` - PostgreSQL async driver
- `redis==5.2.1` - Redis client

**API**:
- `fastapi==0.115.6` - Web framework
- `uvicorn==0.34.0` - ASGI server
- `pydantic==2.10.6` - Data validation

### Service Topology

```
┌─────────────────────┐
│  Frontend (React)   │
│  Port: 3000         │
└──────────┬──────────┘
           │ POST /v1/chat/completions
           ↓
┌─────────────────────┐
│  Traefik Ingress    │
│  Proxy: /api → 8001 │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────────────────┐
│  Backend (FastAPI)              │
│  family-assistant-backend:8001  │
│  Status: Running ✅             │
└─────┬───────────┬───────────┬───┘
      │           │           │
      ↓           ↓           ↓
┌──────────┐ ┌─────────┐ ┌─────────────────┐
│PostgreSQL│ │  Redis  │ │ Mem0:8080       │
│   :5432  │ │  :6379  │ │ Status: Ready ✅│
│   ✅     │ │   ✅    │ └─────────────────┘
└──────────┘ └─────────┘
      │
      ↓
┌──────────────────────────────────┐
│  Qdrant (Vector DB)              │
│  Status: Collections ready ✅    │
└──────────────────────────────────┘
      │
      ↓
┌──────────────────────────────────┐
│  Ollama Embedding Service        │
│  Target: 100.72.98.106:11434     │
│  Status: CONNECTION FAILED ❌    │
└──────────────────────────────────┘
```

---

## Root Cause Hypothesis

### Primary Issue: Service Dependency Failures

**Hypothesis**: Backend is **running and accepting connections** but **failing during request processing** due to:

1. **Embedding Service Unreachable**:
   - Code tries to generate embeddings for semantic memory
   - Connection to `100.72.98.106:11434` fails
   - Error propagates up to chat handler
   - Generic error returned to user

2. **Pydantic Validation Error**:
   - Search/filter operation includes `user_id`
   - Pydantic model rejects it as "extra input"
   - Memory search fails
   - Error propagates up

3. **Error Response Format**:
   - Backend returns 500/error response
   - Response may not include `details` field
   - Frontend doesn't log to console (no `error.details`)
   - User sees generic "I encountered an error" message

### Why No Console Errors?

**Possible Explanations**:
1. Backend returns 200 OK with error in response body (not HTTP error)
2. Error response doesn't match `ChatApiError` structure
3. CORS/network error caught before reaching error handler
4. Generic exception handler catches all errors before specific handlers

---

## Recommendations for Backend Agent

### Immediate Actions Required

#### 1. **Fix Ollama Connection** 🔴 CRITICAL
```bash
# Check what's actually running on that IP
kubectl get pods -A -o wide | grep 100.72.98.106

# Verify Ollama service configuration
kubectl get svc -n llamacpp llamacpp-kimi-vl-service -o yaml

# Check if service DNS resolves correctly
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup llamacpp-kimi-vl-service.llamacpp.svc.cluster.local

# Test connection from backend pod
kubectl exec -it -n homelab deployment/family-assistant-backend -- \
  curl -v http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080/health
```

**Expected Fix**: Update Ollama connection to use Kubernetes service DNS instead of hardcoded IP.

#### 2. **Fix Pydantic Validation** 🔴 CRITICAL

**Locate SearchRequest Model**:
```bash
grep -r "class SearchRequest" services/family-api/src/
```

**Update Model Configuration**:
```python
# Option 1: Allow extra fields (quick fix)
class SearchRequest(BaseModel):
    model_config = ConfigDict(extra='allow')
    filter: dict[str, Any]
    # ... other fields

# Option 2: Explicitly include user_id (proper fix)
class SearchFilter(BaseModel):
    user_id: str
    # ... other filter fields

class SearchRequest(BaseModel):
    filter: SearchFilter
    # ... other fields
```

#### 3. **Improve Error Handling** ⚠️ IMPORTANT

**Add Comprehensive Error Responses**:
```python
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: OpenAIChatRequest):
    try:
        # ... existing code
        result = await agent.chat(...)
        return OpenAIChatResponse(...)

    except ConnectionError as e:
        logger.error(f"Service connection failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service temporarily unavailable",
                "message": "Unable to connect to required services",
                "details": str(e),  # ← Frontend will log this
                "service": "embedding_service"
            }
        )

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "message": "Data validation failed",
                "details": str(e),  # ← Frontend will log this
                "validation_errors": e.errors()
            }
        )

    except Exception as e:
        logger.exception("Unexpected error in chat endpoint")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "details": str(e),  # ← Frontend will log this
                "request_id": "<generate request ID>"
            }
        )
```

#### 4. **Verify Service Endpoints** ⚠️ IMPORTANT
```bash
# Check backend pod is exposing port 8001
kubectl get pod -n homelab -l app=family-assistant-backend -o yaml | grep -A 5 ports

# Verify service selector matches pod labels
kubectl get svc family-assistant-backend -n homelab -o yaml | grep selector
kubectl get pod -n homelab -l app=family-assistant-backend -o yaml | grep labels -A 5

# Test health endpoint
kubectl exec -it -n homelab deployment/family-assistant-backend -- \
  curl http://localhost:8001/health
```

#### 5. **Investigate Port 30880 Service** ℹ️ INFO
```bash
# Find what service uses port 30880
kubectl get svc -A -o wide | grep 30880

# Check if it's a NodePort for Ollama or Mem0
kubectl get svc -n llamacpp -o yaml
kubectl get svc -n homelab -o yaml | grep -A 10 "30880"
```

---

## Testing Strategy

### Step 1: Verify Backend Health
```bash
kubectl exec -it -n homelab deployment/family-assistant-backend -- \
  curl -v http://localhost:8001/health
```

**Expected**: 200 OK with health status

### Step 2: Test Direct Chat Endpoint
```bash
kubectl exec -it -n homelab deployment/family-assistant-backend -- \
  curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "user": "test_user",
    "stream": false
  }'
```

**Expected**: Either successful response OR detailed error with `details` field

### Step 3: Check Ollama Connectivity
```bash
kubectl exec -it -n homelab deployment/family-assistant-backend -- \
  curl -v http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

**Expected**: Embedding response or specific error

### Step 4: Test Frontend → Backend Flow
```bash
# From developer machine (with access to app.fa.pesulabs.net)
curl -X POST https://app.fa.pesulabs.net/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "user": "test",
    "stream": false
  }' | jq
```

**Expected**: Either chat response OR detailed error object

---

## Configuration Files to Review

### Backend Configuration Files
1. **Deployment**: `infrastructure/kubernetes/family-assistant-app/backend-deployment.yaml`
2. **Service**: `infrastructure/kubernetes/family-assistant-app/backend-service.yaml`
3. **Environment Variables**: Check ConfigMap/Secrets for Ollama URL
4. **LLM Service**: `services/family-api/src/api/services/llm_service.py`
5. **Memory Manager**: `services/family-api/src/api/services/memory_manager.py`
6. **Main API**: `services/family-api/src/api/main.py` (already reviewed)

### Critical Environment Variables
```yaml
# Current (from deployment logs):
POSTGRES_HOST: postgres.homelab.svc.cluster.local:5432
REDIS_HOST: redis.homelab.svc.cluster.local:6379
OLLAMA_HOST: http://llamacpp-kimi-vl-service.llamacpp.svc.cluster.local:8080
MEM0_URL: http://mem0.homelab.svc.cluster.local:8080

# Question: Why is code connecting to 100.72.98.106:11434?
# Hypothesis: Code has hardcoded IP or different env var for embeddings
```

---

## Summary for Backend Agent

### What's Working ✅
- Backend service starts successfully
- All Phase 2 services initialize (Redis, Mem0, Qdrant, Ollama startup checks)
- PostgreSQL connection established
- FastAPI server running on port 8001
- Prometheus metrics available
- OpenTelemetry tracing configured

### What's Broken ❌
1. **Embedding service connection fails** at runtime (100.72.98.106:11434)
2. **Pydantic validation error** when filtering by user_id in SearchRequest
3. **Backend service unreachable** from within cluster (connectivity test failed)
4. **Unknown 404 error** on port 30880

### Critical Questions for Backend Agent
1. Why is code trying to connect to `100.72.98.106:11434` instead of Kubernetes service DNS?
2. Where is `SearchRequest` model defined and why doesn't it allow `user_id` in filter?
3. What service runs on port 30880 and why is it returning 404?
4. Is the backend service properly exposing port 8001 to cluster?
5. Why don't errors include `details` field for frontend logging?

### Files to Investigate
1. `src/api/services/llm_service.py` - LLM chat implementation
2. `src/api/services/memory_manager.py` - Memory/search with user filtering
3. `src/api/models/*` - Pydantic models including SearchRequest
4. Backend deployment YAML - Service endpoints and env vars
5. Ollama configuration - Why hardcoded IP instead of service DNS

### Expected Outcome
After fixing these issues, the chat endpoint should:
1. Successfully connect to Ollama for embeddings
2. Properly filter memory by user_id without validation errors
3. Return detailed error responses with `details` field
4. Be accessible from frontend via Traefik proxy

---

## Frontend Context for Reference

### Current Frontend Behavior
- User sends message → Loading state
- Backend responds with error → Generic "I encountered an error while processing your request"
- **No console errors** → Suggests error response lacks `details` field
- Toast notification shows generic message

### What Frontend Expects
```typescript
// Success response
{
  id: string;
  object: "chat.completion";
  created: number;
  model: string;
  choices: [{
    index: 0;
    message: { role: "assistant", content: string };
    finish_reason: "stop";
  }];
}

// Error response (for console logging)
{
  error: string;           // Error type
  message: string;         // User-friendly message
  details: any;            // ← MUST be present for console logging
  [key: string]: any;      // Additional context
}
```

### Frontend Configuration
- **API Base URL**: `/api` (proxied through Traefik)
- **Full Endpoint**: `/api/v1/chat/completions`
- **Request Format**: OpenAI-compatible
- **Auth**: Currently using user_id from OIDC (or 'guest')

---

**End of Report**

**Next Steps**: Backend agent should:
1. Fix Ollama connection configuration
2. Fix Pydantic SearchRequest model
3. Enhance error response format
4. Verify service networking
5. Test end-to-end flow

**Files Created**: `claudedocs/CHAT_TROUBLESHOOTING_REPORT.md`
