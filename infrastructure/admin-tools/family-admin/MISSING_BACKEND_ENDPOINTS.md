# Missing Backend Endpoints

This document tracks which frontend pages are using endpoints that don't exist yet in the backend.

## Status: Updated 2025-11-19

### ✅ Working Endpoints (Available in Backend)

**Authentication**:
- `POST /api/v1/auth/login` ✅
- `POST /api/v1/auth/logout` ✅
- `GET /api/v1/auth/me` ✅

**Family Management**:
- `GET /api/v1/family/members` ✅
- `POST /api/v1/family/members` ✅
- `PUT /api/v1/family/members/{id}` ✅
- `DELETE /api/v1/family/members/{id}` ✅
- `GET /api/v1/family/members/{id}/controls` ✅ (Parental Controls)
- `PUT /api/v1/family/members/{id}/controls` ✅
- `GET /api/v1/family/audit-logs` ✅
- `GET /api/v1/family/content-filter/*` ✅ (Multiple endpoints)

**Phase 2 - Memory & Prompts**:
- `GET /api/phase2/health` ✅
- `GET /api/phase2/stats` ✅
- `POST /api/phase2/memory/search` ✅
- `POST /api/phase2/memory/save` ✅
- `GET /api/phase2/memory/context/{conversation_id}` ✅
- `POST /api/phase2/prompts/build` ✅
- `GET /api/phase2/prompts/core` ✅
- `GET /api/phase2/prompts/role/{role}` ✅
- `GET /api/phase2/users/{user_id}/profile` ✅

**System**:
- `GET /health` ✅
- `GET /api/v1/health` ✅

---

### ❌ Missing Endpoints (Need Backend Implementation)

**Knowledge Base** (Used by Knowledge Center page):
- `GET /api/knowledge` ❌
- `GET /api/knowledge?category={category}` ❌
- `POST /api/knowledge` ❌
- `PUT /api/knowledge/{id}` ❌
- `DELETE /api/knowledge/{id}` ❌
- `GET /api/knowledge/search?q={query}` ❌

**Activity Reports** (Used by MyFamily page):
- `GET /api/reports/activity` ❌
- `GET /api/reports/activity/{user_id}` ❌
- `GET /api/reports/usage` ❌

**Feature Flags** (Used by MyFamily page):
- `GET /api/system/features` ❌
- `PUT /api/system/features/{feature_id}` ❌

**Chat** (Used by Chat page):
- `POST /api/chat/send` ❌
- `GET /api/chat/history/{conversation_id}` ❌
- `DELETE /api/chat/history/{conversation_id}` ❌

**MCP Tools Management** (Used by MCP & Tools page):
- `GET /api/mcp/tools` ❌
- `POST /api/mcp/tools/{tool_id}/connect` ❌
- `POST /api/mcp/tools/{tool_id}/disconnect` ❌
- `POST /api/mcp/tools/{tool_id}/test` ❌
- `PUT /api/mcp/tools/{tool_id}/config` ❌

---

## Impact on Frontend Pages

### Dashboard Page ✅ Working
- Uses Phase 2 health and stats endpoints
- All data fetching successfully

### MyFamily Page ⚠️ Partially Working
- ✅ Family Members tab: Fully functional
- ✅ Parental Controls tab: Fully functional
- ❌ Activity Reports tab: Using mock data (missing `/api/reports/activity`)
- ❌ Feature Flags tab: Using mock data (missing `/api/system/features`)

### Knowledge Center Page ❌ Not Working
- All functionality broken due to missing `/api/knowledge` endpoints
- Frontend will show error: "Path not found: /api/knowledge"

### MCP & Tools Page ❌ Not Working
- All functionality using mock data
- No backend endpoints exist yet

### Chat Page ❌ Not Working
- No chat endpoints implemented yet

### Settings Page 🤷 Unknown
- Haven't checked which endpoints it uses yet

---

## Temporary Frontend Behavior

Until backend endpoints are implemented, the frontend will:

1. **Show error messages** for Knowledge Center (catches 404 errors)
2. **Use mock data** for Activity Reports and Feature Flags (with warning banners)
3. **Use mock data** for MCP & Tools (with warning banner)
4. **Chat page** may show errors when trying to send messages

---

## Recommended Priority for Backend Implementation

1. **High Priority**: `/api/knowledge/*` - Knowledge Center is a key feature
2. **Medium Priority**: `/api/reports/activity` - Complete MyFamily page functionality
3. **Medium Priority**: `/api/chat/*` - Enable chat interface
4. **Low Priority**: `/api/system/features` - Feature flags less critical
5. **Low Priority**: `/api/mcp/tools/*` - MCP management can use mock data for now

---

## Notes

- All family management endpoints are properly prefixed with `/api/v1/`
- Phase 2 endpoints use `/api/phase2/` prefix
- The frontend API client has been updated to use correct paths for family endpoints
- Knowledge Center and other missing endpoints will gracefully show errors until backend is ready
