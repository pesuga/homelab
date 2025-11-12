# Phase 2 Integration Instructions

## Overview

This document provides step-by-step instructions to integrate Phase 2 (System Prompts & Memory Architecture) with the existing Family Assistant API.

## Files Created

### Core Services
- `api/services/memory_manager.py` - 5-layer memory orchestration
- `api/services/prompt_builder.py` - Dynamic prompt assembly

### API Layer
- `api/models/memory.py` - Pydantic models for Phase 2
- `api/routes/phase2_routes.py` - API routes for memory and prompts
- `api/startup.py` - Service initialization

### Prompts
- `prompts/core/` - Core system prompts
- `prompts/roles/` - Role-specific prompts
- `prompts/languages/` - Bilingual context

## Integration Steps

### Step 1: Update main.py Imports

Add these imports after the existing imports (around line 27):

```python
# Phase 2: Memory & Prompt Management
from api.routes.phase2_routes import router as phase2_router
from api.startup import startup_event, shutdown_event
```

### Step 2: Include Phase 2 Router

Add this line after the CORS middleware setup (around line 46):

```python
# Include Phase 2 routes
app.include_router(phase2_router)
```

### Step 3: Add Startup and Shutdown Events

Add these event handlers before the main.py endpoint definitions (around line 48):

```python
# ==============================================================================
# Application Lifecycle Events
# ==============================================================================

@app.on_event("startup")
async def on_startup():
    """Initialize services on application startup"""
    print("=" * 80)
    print("FAMILY ASSISTANT API STARTING")
    print("=" * 80)
    await startup_event()


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup services on application shutdown"""
    await shutdown_event()
```

### Step 4: Update requirements.txt

Add these dependencies if not already present:

```
redis>=5.0.0
qdrant-client>=1.7.0
```

### Step 5: Environment Variables

Add to your `.env` file (or update settings):

```bash
# Phase 2: Memory Services
REDIS_URL=redis://redis.homelab.svc.cluster.local:6379
MEM0_URL=http://100.81.76.55:30880
QDRANT_URL=http://100.81.76.55:30633
OLLAMA_URL=http://100.72.98.106:11434
```

## Complete Integration Patch

Here's the complete patch to apply to `api/main.py`:

```python
# After line 27 (after existing imports):
# Phase 2: Memory & Prompt Management
from api.routes.phase2_routes import router as phase2_router
from api.startup import startup_event, shutdown_event

# After line 46 (after CORS middleware):
# Include Phase 2 routes
app.include_router(phase2_router)

# After line 47 (before endpoint definitions):
# ==============================================================================
# Application Lifecycle Events
# ==============================================================================

@app.on_event("startup")
async def on_startup():
    """Initialize services on application startup"""
    print("=" * 80)
    print("FAMILY ASSISTANT API STARTING")
    print("=" * 80)
    await startup_event()


@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup services on application shutdown"""
    await shutdown_event()
```

## Verification Steps

### 1. Test API Startup

```bash
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant
python -m api.main
```

Expected output:
```
================================================================================
FAMILY ASSISTANT API STARTING
================================================================================
🚀 Initializing Phase 2 services...
  📦 Initializing MemoryManager (5-layer architecture)...
    ✅ Redis connection established
    ✅ Mem0 client ready
    ✅ Qdrant collections initialized
    ✅ Ollama embedding service connected
  📝 Initializing PromptBuilder...
    ✅ Prompt templates loaded
    ✅ Role prompts cached
    ✅ Bilingual context ready
✅ Phase 2 services initialized successfully!
```

### 2. Test API Endpoints

**Health Check**:
```bash
curl http://localhost:8001/api/phase2/health
```

**Core Prompt**:
```bash
curl http://localhost:8001/api/phase2/prompts/core
```

**Role Prompt**:
```bash
curl http://localhost:8001/api/phase2/prompts/role/parent
```

**Memory Search**:
```bash
curl -X POST http://localhost:8001/api/phase2/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "calendar events",
    "user_id": "test-user",
    "limit": 10
  }'
```

**Build Prompt**:
```bash
curl -X POST http://localhost:8001/api/phase2/prompts/build \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "conversation_id": "test-conv",
    "minimal": false
  }'
```

**Test Prompt Assembly** (useful for debugging):
```bash
curl "http://localhost:8001/api/phase2/test/prompt-assembly?user_id=test&role=parent&language=es"
```

### 3. Test with Docker

Update Dockerfile if needed (should already work):

```dockerfile
# Should already include Phase 2 code via COPY
COPY . .
```

Build and test:
```bash
cd /home/pesu/Rakuflow/systems/homelab/services/family-assistant
docker build -t family-assistant:phase2-test .
docker run -p 8001:8001 \
  -e REDIS_URL=redis://100.81.76.55:6379 \
  -e MEM0_URL=http://100.81.76.55:30880 \
  -e QDRANT_URL=http://100.81.76.55:30633 \
  -e OLLAMA_URL=http://100.72.98.106:11434 \
  family-assistant:phase2-test
```

## API Documentation

Once integrated, Phase 2 endpoints will be available at:

**Interactive Docs**: http://localhost:8001/docs
**OpenAPI Spec**: http://localhost:8001/openapi.json

Phase 2 endpoints under `/api/phase2`:
- `/memory/search` - Search memories
- `/memory/save` - Save context
- `/memory/context/{conversation_id}` - Get conversation context
- `/prompts/build` - Build dynamic prompt
- `/prompts/role/{role}` - Get role prompt
- `/prompts/core` - Get core prompt
- `/users/{user_id}/profile` - Get/update user profile
- `/health` - Memory system health check
- `/stats` - Memory system statistics
- `/test/prompt-assembly` - Test prompt assembly

## Troubleshooting

### Issue: Redis Connection Failed

**Solution**: Check Redis service is running:
```bash
kubectl get pods -n homelab -l app=redis
```

### Issue: Qdrant Collections Not Found

**Solution**: Collections are created automatically on startup. Check logs for initialization errors.

### Issue: Mem0 Service Unavailable

**Solution**: Verify Mem0 service:
```bash
curl http://100.81.76.55:30880/health
```

### Issue: Ollama Embedding Generation Fails

**Solution**: Ensure nomic-embed-text model is loaded:
```bash
curl http://100.72.98.106:11434/api/tags
```

If not present:
```bash
ollama pull nomic-embed-text
```

## Database Migration (Optional for Phase 2)

Phase 2 works with existing database schema. For full functionality, run migration:

```sql
-- See database/migrations/phase2_schema.sql for complete migration
ALTER TABLE family_members ADD COLUMN role VARCHAR(20) DEFAULT 'member';
ALTER TABLE family_members ADD COLUMN language_preference VARCHAR(10) DEFAULT 'en';
-- ... (additional schema changes)
```

## Next Steps

After integration:

1. **Test with Real Data**: Use actual Telegram bot interactions
2. **Monitor Performance**: Check memory retrieval latency
3. **Tune Prompts**: Adjust role prompts based on family feedback
4. **Implement Skills**: Add calendar, reminders, homework help skills (Phase 4)
5. **Add User Management**: Implement family IAM (Phase 3)

## Support

For issues or questions:
- Check logs in `/home/pesu/Rakuflow/systems/homelab/services/family-assistant/logs/`
- Review Phase 2 documentation in `PHASE2_COMPLETE.md`
- Test endpoints using `test/prompt-assembly` endpoint
