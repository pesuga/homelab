"""
Personal MCP API Routes

User-facing API for managing personal MCP servers and tools.
Integrates with arcade.dev for tool discovery and execution.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_from_token, get_db_pool
from api.models.user_management import FamilyMember
from api.services.personal_mcp_manager import (
    PersonalMCPManager, PersonalMCPServer, PersonalMCPTool,
    PersonalMCPServerStatus
)
import asyncpg


router = APIRouter(prefix="/api/v1/personal-mcp", tags=["Personal MCP"])


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ArcadeDevServer(BaseModel):
    """Model for arcade.dev discovered server"""
    id: str
    name: str
    description: Optional[str]
    category: str = "general"
    tool_count: int
    requires_auth: bool
    source: str = "arcade_dev"


class PersonalMCPServerCreate(BaseModel):
    """Model for creating a new personal MCP server"""
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    connection_type: str = Field(..., description="arcade or local")


class ArcadeServerConnect(BaseModel):
    """Model for connecting to arcade.dev server"""
    arcade_server_id: str
    server_name: str
    description: Optional[str] = None


class LocalServerCreate(BaseModel):
    """Model for creating a local MCP server"""
    name: str
    description: Optional[str] = None
    command: str
    args: List[str] = Field(default_factory=list)


class PersonalMCPToolExecute(BaseModel):
    """Model for executing a personal MCP tool"""
    server_id: str
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None


class AuthTokenStore(BaseModel):
    """Model for storing authentication tokens"""
    platform: str
    auth_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None


class PersonalMCPServerResponse(BaseModel):
    """Response model for personal MCP server"""
    id: str
    name: str
    description: Optional[str]
    connection_type: str
    status: PersonalMCPServerStatus
    tool_count: int
    last_connected: Optional[str]
    is_active: bool
    created_at: str


# ============================================================================
# Dependencies
# ============================================================================

async def get_personal_mcp_manager(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> PersonalMCPManager:
    """Get personal MCP manager instance"""
    from api.services.personal_mcp_manager import create_personal_mcp_manager
    return await create_personal_mcp_manager(db_pool)


# ============================================================================
# Arcade.dev Integration Endpoints
# ============================================================================

@router.get("/arcade/discover", response_model=List[ArcadeDevServer])
async def discover_arcade_servers(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Discover available MCP servers from arcade.dev"""
    try:
        servers = await mcp_manager.discover_arcade_servers(str(current_user.id))
        return [ArcadeDevServer(**server) for server in servers]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover servers: {str(e)}"
        )


@router.post("/arcade/connect", response_model=Dict[str, str])
async def connect_arcade_server(
    connection_data: ArcadeServerConnect,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Connect to an arcade.dev MCP server"""
    try:
        server_id = await mcp_manager.connect_arcade_server(
            user_id=str(current_user.id),
            arcade_server_id=connection_data.arcade_server_id,
            server_name=connection_data.server_name,
            description=connection_data.description
        )

        return {
            "message": "Successfully connected to arcade.dev server",
            "server_id": server_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to server: {str(e)}"
        )


@router.post("/arcade/auth/store", response_model=Dict[str, str])
async def store_arcade_auth_token(
    auth_data: AuthTokenStore,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Store arcade.dev authentication token"""
    try:
        from datetime import datetime
        expires_at = None
        if auth_data.expires_at:
            expires_at = datetime.fromisoformat(auth_data.expires_at)

        await mcp_manager.store_auth_token(
            user_id=str(current_user.id),
            platform=auth_data.platform,
            auth_token=auth_data.auth_token,
            refresh_token=auth_data.refresh_token,
            expires_at=expires_at
        )

        return {"message": "Authentication token stored successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store auth token: {str(e)}"
        )


# ============================================================================
# Local MCP Server Management
# ============================================================================

@router.post("/servers/local", response_model=Dict[str, str])
async def add_local_mcp_server(
    server_data: LocalServerCreate,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Add a local MCP server"""
    try:
        server_id = await mcp_manager.add_local_mcp_server(
            user_id=str(current_user.id),
            name=server_data.name,
            command=server_data.command,
            args=server_data.args,
            description=server_data.description
        )

        return {
            "message": "Local MCP server added successfully",
            "server_id": server_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add local server: {str(e)}"
        )


# ============================================================================
# Personal MCP Server Management
# ============================================================================

@router.get("/servers", response_model=List[PersonalMCPServerResponse])
async def list_personal_mcp_servers(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """List all personal MCP servers for the current user"""
    try:
        servers = await mcp_manager.get_user_servers(str(current_user.id))

        response_servers = []
        for server in servers:
            response_server = PersonalMCPServerResponse(
                id=server.id,
                name=server.name,
                description=server.description,
                connection_type=server.connection_type,
                status=server.status,
                tool_count=len(server.tools),
                last_connected=server.last_connected.isoformat() if server.last_connected else None,
                is_active=server.is_active,
                created_at=server.created_at.isoformat()
            )
            response_servers.append(response_server)

        return response_servers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        )


@router.get("/servers/{server_id}", response_model=Dict[str, Any])
async def get_personal_mcp_server(
    server_id: str,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Get details of a specific personal MCP server"""
    try:
        servers = await mcp_manager.get_user_servers(str(current_user.id))
        server = next((s for s in servers if s.id == server_id), None)

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found"
            )

        return {
            "id": server.id,
            "name": server.name,
            "description": server.description,
            "connection_type": server.connection_type,
            "status": server.status.value,
            "tools": [tool.dict() for tool in server.tools],
            "last_connected": server.last_connected.isoformat() if server.last_connected else None,
            "error_message": server.error_message,
            "is_active": server.is_active,
            "created_at": server.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server details: {str(e)}"
        )


@router.delete("/servers/{server_id}")
async def disconnect_personal_mcp_server(
    server_id: str,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Disconnect a personal MCP server"""
    try:
        success = await mcp_manager.disconnect_server(str(current_user.id), server_id)

        if success:
            return {"message": "Server disconnected successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Server not found or already disconnected"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect server: {str(e)}"
        )


# ============================================================================
# Personal MCP Tool Execution
# ============================================================================

@router.post("/tools/execute")
async def execute_personal_mcp_tool(
    execution_data: PersonalMCPToolExecute,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Execute a personal MCP tool"""
    try:
        result = await mcp_manager.execute_personal_tool(
            user_id=str(current_user.id),
            server_id=execution_data.server_id,
            tool_name=execution_data.tool_name,
            parameters=execution_data.parameters,
            conversation_id=execution_data.conversation_id
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool: {str(e)}"
        )


@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_available_tools(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """List all available tools from user's connected servers"""
    try:
        servers = await mcp_manager.get_user_servers(str(current_user.id))

        all_tools = []
        for server in servers:
            if server.status == PersonalMCPServerStatus.CONNECTED:
                for tool in server.tools:
                    all_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "server_name": tool.server_name,
                        "server_id": server.id,
                        "category": tool.category,
                        "parameters": tool.parameters,
                        "personal_data_access": tool.personal_data_access,
                        "safety_level": tool.safety_level,
                        "requires_auth": tool.requires_auth
                    })

        return all_tools
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


# ============================================================================
# Personal MCP Analytics and Usage
# ============================================================================

@router.get("/analytics/usage")
async def get_usage_analytics(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Get usage analytics for personal MCP tools"""
    try:
        stats = await mcp_manager.get_tool_usage_stats(str(current_user.id), days)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage analytics: {str(e)}"
        )


@router.get("/analytics/recent-activity")
async def get_recent_activity(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    limit: int = Query(50, description="Maximum number of activities", ge=1, le=200)
):
    """Get recent tool execution activity"""
    try:
        rows = await db_pool.fetch("""
            SELECT
                ptu.execution_id,
                ptu.tool_name,
                ps.name as server_name,
                ptu.success,
                ptu.result,
                ptu.error_message,
                ptu.execution_time_ms,
                ptu.timestamp,
                ptu.personal_data_accessed
            FROM personal_mcp_tool_usage ptu
            JOIN personal_mcp_servers ps ON ptu.server_id = ps.id
            WHERE ptu.user_id = $1
            ORDER BY ptu.timestamp DESC
            LIMIT $2
        """, str(current_user.id), limit)

        activities = []
        for row in rows:
            activities.append({
                "execution_id": row["execution_id"],
                "tool_name": row["tool_name"],
                "server_name": row["server_name"],
                "success": row["success"],
                "result": row["result"],
                "error_message": row["error_message"],
                "execution_time_ms": row["execution_time_ms"],
                "timestamp": row["timestamp"].isoformat(),
                "personal_data_accessed": row["personal_data_accessed"]
            })

        return activities
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activity: {str(e)}"
        )


# ============================================================================
# Tool Categories and Discovery
# ============================================================================

@router.get("/categories")
async def get_tool_categories(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Get available tool categories from user's servers"""
    try:
        servers = await mcp_manager.get_user_servers(str(current_user.id))

        categories = set()
        category_counts = {}

        for server in servers:
            if server.status == PersonalMCPServerStatus.CONNECTED:
                for tool in server.tools:
                    category = tool.category
                    categories.add(category)
                    category_counts[category] = category_counts.get(category, 0) + 1

        result = []
        for category in sorted(categories):
            result.append({
                "name": category,
                "tool_count": category_counts[category],
                "description": _get_category_description(category)
            })

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


def _get_category_description(category: str) -> str:
    """Get description for a tool category"""
    descriptions = {
        "calendar": "Calendar and scheduling tools",
        "notes": "Note-taking and documentation tools",
        "productivity": "Productivity and task management tools",
        "communication": "Communication and messaging tools",
        "development": "Development and coding tools",
        "file_management": "File and storage management tools",
        "automation": "Automation and workflow tools",
        "finance": "Financial and budgeting tools",
        "health": "Health and fitness tracking tools",
        "education": "Learning and educational tools",
        "entertainment": "Entertainment and media tools",
        "general": "General purpose tools"
    }
    return descriptions.get(category, "Custom tools and utilities")


@router.get("/tools/by-category/{category}")
async def get_tools_by_category(
    category: str,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: PersonalMCPManager = Depends(get_personal_mcp_manager)
):
    """Get tools from a specific category"""
    try:
        servers = await mcp_manager.get_user_servers(str(current_user.id))

        category_tools = []
        for server in servers:
            if server.status == PersonalMCPServerStatus.CONNECTED:
                for tool in server.tools:
                    if tool.category == category:
                        category_tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "server_name": tool.server_name,
                            "server_id": server.id,
                            "parameters": tool.parameters,
                            "personal_data_access": tool.personal_data_access,
                            "safety_level": tool.safety_level
                        })

        return {
            "category": category,
            "tool_count": len(category_tools),
            "tools": category_tools
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tools by category: {str(e)}"
        )


# ============================================================================
# Configuration and Setup Help
# ============================================================================

@router.get("/setup-guide")
async def get_setup_guide():
    """Get setup guide for personal MCP servers"""
    return {
        "title": "Personal MCP Setup Guide",
        "description": "Connect your personal tools to extend Family Assistant capabilities",
        "methods": [
            {
                "name": "Arcade.dev Integration",
                "description": "Connect to pre-built MCP servers from arcade.dev",
                "steps": [
                    "1. Create an account on arcade.dev",
                    "2. Discover available MCP servers",
                    "3. Connect your preferred servers with one click",
                    "4. Start using your tools in Family Assistant"
                ],
                "benefits": ["Easy setup", "Pre-configured tools", "No technical knowledge required"]
            },
            {
                "name": "Local MCP Server",
                "description": "Connect your own locally running MCP server",
                "steps": [
                    "1. Install and run your MCP server locally",
                    "2. Add the server configuration in Family Assistant",
                    "3. Test the connection",
                    "4. Use your custom tools"
                ],
                "benefits": ["Full control", "Custom tools", "Privacy", "No external dependencies"]
            }
        ],
        "supported_categories": [
            "Calendar", "Notes", "Productivity", "Communication",
            "Development", "File Management", "Automation", "Finance"
        ],
        "safety_features": [
            "Role-based access control",
            "Personal data protection",
            "Execution logging",
            "Safety level classification",
            "Error handling and recovery"
        ]
    }