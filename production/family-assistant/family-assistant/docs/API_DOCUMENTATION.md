# Family Assistant API Documentation

## Overview
The Family Assistant API (v2.0.0) provides a comprehensive, privacy-focused AI assistant with MCP integration, family management, and multimodal support.

## Quick Start

### Base URLs
- **Production**: `https://admin.homelab.pesulabs.net`
- **Development**: `http://localhost:8000`

### Authentication
- **Type**: JWT Bearer Token
- **Roles**: `parent`, `grandparent`, `teenager`, `child`
- **Admin Access**: Required for MCP configuration endpoints

### Documentation
- **Swagger UI**: `/docs` (Interactive API documentation)
- **ReDoc**: `/redoc` (Alternative documentation view)
- **OpenAPI JSON**: `/openapi.json` (Raw API specification)

## Core Endpoints

### Health & Info
- `GET /` - API root with navigation links
- `GET /health` - Service health status
- `GET /api/info` - Detailed API capabilities and endpoints

### Chat & Conversations
- `POST /chat` - Enhanced chat with multimodal support
- `POST /v1/chat/completions` - OpenAI-compatible chat (for LobeChat)
- `GET /v1/models` - Available models
- `GET /conversations/{thread_id}` - Get conversation history
- `POST /upload` - Multimodal content upload (images, audio, documents)

## Two-Tier MCP System

### Admin Configuration (`/api/v1/admin/mcp/*`)
**Admin-only endpoints for system-wide MCP management:**

- `POST /api/v1/admin/mcp/arcade/configure` - Configure arcade.dev integration
- `POST /api/v1/admin/mcp/arcade/sync` - Sync arcade.dev servers
- `GET /api/v1/admin/mcp/arcade/status` - Get arcade.dev status
- `GET /api/v1/admin/mcp/servers` - List all MCP servers
- `POST /api/v1/admin/mcp/servers/custom` - Add custom MCP server
- `GET /api/v1/admin/mcp/tools/available` - List available tools
- `PUT /api/v1/admin/mcp/tools/permissions` - Update tool permissions
- `GET /api/v1/admin/mcp/analytics/usage` - Usage analytics
- `GET /api/v1/admin/mcp/config/overview` - System configuration overview
- `GET /api/v1/admin/mcp/setup-guide` - Admin setup guide

### Family Member Access (`/api/v1/family-tools/*`)
**Simplified interface for family members:**

- `GET /api/v1/family-tools/tools` - Browse available tools
- `POST /api/v1/family-tools/tools/execute` - Execute a tool
- `GET /api/v1/family-tools/favorites` - Get favorite tools
- `POST /api/v1/family-tools/favorites` - Add tool to favorites
- `DELETE /api/v1/family-tools/favorites` - Remove favorite
- `GET /api/v1/family-tools/recommendations` - Get personalized recommendations
- `GET /api/v1/family-tools/history` - Tool usage history
- `GET /api/v1/family-tools/categories` - Tool categories

## Dashboard & Monitoring (`/dashboard/*`)

- `GET /dashboard/system-health` - Comprehensive system health
- `GET /dashboard/services` - Service status overview
- `GET /dashboard/metrics` - System metrics (CPU, memory, disk)
- `GET /dashboard/architecture` - Architecture documentation
- `GET /dashboard/recent-activity` - Recent system activity
- `GET /dashboard/stats` - Overall statistics
- `WS /ws` - Real-time updates via WebSocket
- `POST /dashboard/alerts/dismiss` - Dismiss system alerts

## Family Management (`/api/v1/family/*`)

- `GET /api/v1/family/members` - List family members
- `POST /api/v1/family/members` - Add family member
- `GET /api/v1/family/members/{user_id}` - Get member details
- `PUT /api/v1/family/members/{user_id}` - Update member
- `DELETE /api/v1/family/members/{user_id}` - Remove member
- `GET /api/v1/family/permissions/{role}` - Get role permissions
- `PUT /api/v1/family/permissions/{role}` - Update role permissions

## Feature Flags (`/features/*`)

- `GET /features` - Get available features for user
- `GET /features/statistics` - Feature usage statistics
- `GET /features/export` - Export feature configuration
- `POST /features/{flag_key}/enable` - Enable feature (admin)
- `POST /features/{flag_key}/disable` - Disable feature (admin)
- `GET /features/{flag_key}` - Get detailed flag configuration

## Memory System (`/api/v1/memory/*`)

- `GET /api/v1/memory/search` - Search memories
- `POST /api/v1/memory/store` - Store memory
- `GET /api/v1/memory/recent` - Recent memories
- `DELETE /api/v1/memory/{memory_id}` - Delete memory

## Authentication (`/api/v1/auth/*`)

- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `GET /api/v1/auth/me` - Get current user profile

## MCP Integration Examples

### Admin Setup (arcade.dev)
```bash
# Configure arcade.dev integration
curl -X POST "https://admin.homelab.pesulabs.net/api/v1/admin/mcp/arcade/configure" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "api_token": "arcade_dev_token_here",
    "auto_sync": true
  }'

# Sync servers
curl -X POST "https://admin.homelab.pesulabs.net/api/v1/admin/mcp/arcade/sync" \
  -H "Authorization: Bearer {admin_token}"
```

### Family Member Usage
```bash
# Browse available tools
curl -X GET "https://admin.homelab.pesulabs.net/api/v1/family-tools/tools" \
  -H "Authorization: Bearer {user_token}"

# Execute a tool
curl -X POST "https://admin.homelab.pesulabs.net/api/v1/family-tools/tools/execute" \
  -H "Authorization: Bearer {user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "weather",
    "parameters": {"location": "New York"}
  }'
```

## Database Schema

The MCP system uses the following key tables:

### Admin Layer
- `admin_mcp_servers` - Global MCP server configuration
- `admin_arcade_config` - Encrypted arcade.dev settings
- `system_tool_availability` - Tool permissions and risk levels

### Family Member Layer
- `family_tool_executions` - Tool usage tracking
- `family_tool_favorites` - Personal tool favorites
- `family_tool_recommendations` - Automated recommendations
- `parental_approval_requests` - Approval workflow for high-risk tools

## Family Safety Features

### Role-Based Access Control
- **Parents**: Full access to all tools and configuration
- **Grandparents**: Full access to family-safe tools
- **Teenagers**: Access to approved tools, some restrictions
- **Children**: Restricted access, parental approval required for most tools

### Parental Controls
- Automatic approval requirements for high-risk tools
- Personal data access auditing
- Usage analytics and reporting
- Cost controls and usage limits

## Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error responses follow this format:
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2025-01-17T12:00:00Z"
}
```

## Rate Limiting

- **Authenticated users**: 100 requests per minute
- **Admin endpoints**: 200 requests per minute
- **Chat endpoints**: 30 requests per minute per user

## Support

- **Documentation**: https://admin.homelab.pesulabs.net/docs
- **Health Check**: https://admin.homelab.pesulabs.net/health
- **Admin Email**: admin@pesulabs.net

## Changelog

### v2.0.0 (Current)
- ✅ Two-tier MCP system implementation
- ✅ Admin MCP configuration with arcade.dev integration
- ✅ Family member tool discovery interface
- ✅ Enhanced OpenAPI documentation
- ✅ Comprehensive database schema for MCP system
- ✅ Family safety controls and parental oversight
- ✅ Usage analytics and cost tracking

### v1.0.0
- ✅ Basic chat functionality
- ✅ JWT authentication
- ✅ Family member management
- ✅ System monitoring dashboard