"""
MCP (Model Context Protocol) API Routes

Provides REST API endpoints for managing MCP servers, tools,
and execution with proper authentication and RBAC.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import (
    get_current_user_from_token,
    get_current_admin_user,
    get_db_pool
)
from api.models.user_management import FamilyMember
from api.services.mcp_manager import (
    MCPServerManager, MCPExecutionEngine,
    MCPServer, MCPTool, MCPExecutionContext, MCPExecutionResult,
    MCPServerStatus
)
import asyncpg


router = APIRouter(prefix="/api/v1/mcp", tags=["MCP Management"])


# ============================================================================
# Pydantic Models for API
# ============================================================================

class MCPServerCreate(BaseModel):
    """Model for creating a new MCP server"""
    name: str = Field(..., description="Unique server name")
    command: str = Field(..., description="Command to start MCP server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class MCPServerResponse(BaseModel):
    """Response model for MCP server data"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    status: MCPServerStatus
    tools: List[MCPTool]
    pid: Optional[int]
    last_health_check: Optional[str]
    error_message: Optional[str]


class MCPToolExecuteRequest(BaseModel):
    """Model for tool execution request"""
    tool_name: str = Field(..., description="Name of tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")


class MCPMetricsResponse(BaseModel):
    """Response model for MCP metrics"""
    total_servers: int
    online_servers: int
    total_tools: int
    total_executions_today: int
    success_rate_today: float
    top_used_tools: List[Dict[str, Any]]
    usage_by_role: Dict[str, int]


class MCPPermissionUpdate(BaseModel):
    """Model for updating tool permissions"""
    tool_name: str
    server_name: str
    role: str
    can_execute: bool


# ============================================================================
# Dependencies
# ============================================================================

async def get_mcp_manager(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> MCPServerManager:
    """Get MCP server manager instance"""
    from api.services.mcp_manager import create_mcp_manager
    return await create_mcp_manager(db_pool)


async def get_mcp_execution_engine(
    mcp_manager: MCPServerManager = Depends(get_mcp_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> MCPExecutionEngine:
    """Get MCP execution engine instance"""
    from api.services.mcp_manager import create_mcp_execution_engine
    return await create_mcp_execution_engine(db_pool, mcp_manager)


# ============================================================================
# MCP Server Management Endpoints
# ============================================================================

@router.get("/servers", response_model=List[MCPServerResponse])
async def list_mcp_servers(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """List all registered MCP servers"""
    servers = []

    for server in mcp_manager.servers.values():
        server_response = MCPServerResponse(
            name=server.name,
            command=server.command,
            args=server.args,
            env=server.env,
            status=server.status,
            tools=server.tools,
            pid=server.pid,
            last_health_check=server.last_health_check.isoformat() if server.last_health_check else None,
            error_message=server.error_message
        )
        servers.append(server_response)

    return servers


@router.post("/servers", response_model=Dict[str, str])
async def register_mcp_server(
    server_data: MCPServerCreate,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Register a new MCP server (admin only)"""
    server = MCPServer(
        name=server_data.name,
        command=server_data.command,
        args=server_data.args,
        env=server_data.env
    )

    success = await mcp_manager.register_server(server)

    if success:
        return {"message": f"MCP server '{server.name}' registered successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register MCP server"
        )


@router.post("/servers/{server_name}/start")
async def start_mcp_server(
    server_name: str,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Start an MCP server (admin only)"""
    success = await mcp_manager.start_server(server_name)

    if success:
        return {"message": f"MCP server '{server_name}' started successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start MCP server '{server_name}'"
        )


@router.post("/servers/{server_name}/stop")
async def stop_mcp_server(
    server_name: str,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Stop an MCP server (admin only)"""
    success = await mcp_manager.stop_server(server_name)

    if success:
        return {"message": f"MCP server '{server_name}' stopped successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to stop MCP server '{server_name}'"
        )


@router.delete("/servers/{server_name}")
async def delete_mcp_server(
    server_name: str,
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Delete an MCP server (admin only)"""

    # Stop server if running
    if server_name in mcp_manager.running_processes:
        await mcp_manager.stop_server(server_name)

    # Delete from database
    result = await db_pool.execute(
        "DELETE FROM mcp_servers WHERE name = $1",
        server_name
    )

    if result == "DELETE 1":
        # Remove from manager
        if server_name in mcp_manager.servers:
            del mcp_manager.servers[server_name]

        return {"message": f"MCP server '{server_name}' deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_name}' not found"
        )


# ============================================================================
# MCP Tool Management Endpoints
# ============================================================================

@router.get("/tools", response_model=List[MCPTool])
async def list_mcp_tools(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """List all available MCP tools (filtered by user permissions)"""
    all_tools = []

    for server in mcp_manager.servers.values():
        for tool in server.tools:
            # Check if user can execute this tool
            can_execute, _ = await mcp_manager.execution_engine.can_user_execute_tool(
                str(current_user.id), tool.name, server.name
            )

            if can_execute:
                all_tools.append(tool)

    return all_tools


@router.get("/tools/{tool_name}", response_model=MCPTool)
async def get_mcp_tool(
    tool_name: str,
    server_name: str = Query(..., description="MCP server name"),
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Get details for a specific MCP tool"""

    # Find the tool
    tool = None
    for server in mcp_manager.servers.values():
        if server.name == server_name:
            for t in server.tools:
                if t.name == tool_name:
                    tool = t
                    break
            if tool:
                break

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found on server '{server_name}'"
        )

    # Check permissions
    can_execute, _ = await mcp_manager.execution_engine.can_user_execute_tool(
        str(current_user.id), tool_name, server_name
    )

    if not can_execute:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this tool"
        )

    return tool


@router.post("/tools/execute", response_model=MCPExecutionResult)
async def execute_mcp_tool(
    request: MCPToolExecuteRequest,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    execution_engine: MCPExecutionEngine = Depends(get_mcp_execution_engine)
):
    """Execute an MCP tool"""

    context = MCPExecutionContext(
        user_id=str(current_user.id),
        tool_name=request.tool_name,
        parameters=request.parameters,
        conversation_id=request.conversation_id
    )

    result = await execution_engine.execute_tool(context)

    return result


# ============================================================================
# MCP Permission Management Endpoints (Admin Only)
# ============================================================================

@router.get("/permissions")
async def list_mcp_permissions(
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """List all MCP tool permissions (admin only)"""

    rows = await db_pool.fetch("""
        SELECT tool_name, server_name, role, can_execute
        FROM mcp_tool_permissions
        ORDER BY server_name, tool_name, role
    """)

    permissions = []
    for row in rows:
        permissions.append({
            "tool_name": row['tool_name'],
            "server_name": row['server_name'],
            "role": row['role'],
            "can_execute": row['can_execute']
        })

    return permissions


@router.post("/permissions")
async def update_mcp_permission(
    permission_data: MCPPermissionUpdate,
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Update MCP tool permission (admin only)"""

    # Upsert permission
    await db_pool.execute("""
        INSERT INTO mcp_tool_permissions (tool_name, server_name, role, can_execute)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (tool_name, server_name, role)
        DO UPDATE SET can_execute = $4
    """, permission_data.tool_name, permission_data.server_name,
        permission_data.role, permission_data.can_execute)

    return {"message": "Permission updated successfully"}


@router.delete("/permissions/{tool_name}/{server_name}/{role}")
async def delete_mcp_permission(
    tool_name: str,
    server_name: str,
    role: str,
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Delete MCP tool permission (admin only)"""

    result = await db_pool.execute("""
        DELETE FROM mcp_tool_permissions
        WHERE tool_name = $1 AND server_name = $2 AND role = $3
    """, tool_name, server_name, role)

    if result == "DELETE 1":
        return {"message": "Permission deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )


# ============================================================================
# MCP Metrics and Monitoring Endpoints
# ============================================================================

@router.get("/metrics", response_model=MCPMetricsResponse)
async def get_mcp_metrics(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get MCP usage metrics and statistics"""

    # Server statistics
    total_servers = len(mcp_manager.servers)
    online_servers = sum(
        1 for server in mcp_manager.servers.values()
        if server.status == MCPServerStatus.ONLINE
    )

    # Tool statistics
    total_tools = sum(
        len(server.tools) for server in mcp_manager.servers.values()
    )

    # Usage statistics
    today_start = "2025-11-17 00:00:00"  # Today's date

    # Total executions today
    total_executions_today = await db_pool.fetchval("""
        SELECT COUNT(*) FROM mcp_tool_usage
        WHERE DATE(timestamp) = CURRENT_DATE
    """)

    # Success rate today
    successful_executions = await db_pool.fetchval("""
        SELECT COUNT(*) FROM mcp_tool_usage
        WHERE DATE(timestamp) = CURRENT_DATE AND success = true
    """)

    success_rate_today = (
        (successful_executions / total_executions_today * 100)
        if total_executions_today > 0 else 0
    )

    # Top used tools today
    top_tools = await db_pool.fetch("""
        SELECT tool_name, COUNT(*) as usage_count
        FROM mcp_tool_usage
        WHERE DATE(timestamp) = CURRENT_DATE AND success = true
        GROUP BY tool_name
        ORDER BY usage_count DESC
        LIMIT 10
    """)

    top_used_tools = [
        {"tool_name": row['tool_name'], "usage_count": row['usage_count']}
        for row in top_tools
    ]

    # Usage by role
    role_usage = await db_pool.fetch("""
        SELECT fm.role, COUNT(*) as usage_count
        FROM mcp_tool_usage mu
        JOIN family_members fm ON mu.user_id = fm.id
        WHERE DATE(mu.timestamp) = CURRENT_DATE
        GROUP BY fm.role
    """)

    usage_by_role = {
        row['role']: row['usage_count'] for row in role_usage
    }

    return MCPMetricsResponse(
        total_servers=total_servers,
        online_servers=online_servers,
        total_tools=total_tools,
        total_executions_today=total_executions_today,
        success_rate_today=round(success_rate_today, 2),
        top_used_tools=top_used_tools,
        usage_by_role=usage_by_role
    )


@router.get("/usage")
async def get_mcp_usage_history(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    days: int = Query(7, description="Number of days to include", ge=1, le=30)
):
    """Get MCP usage history for the last N days"""

    rows = await db_pool.fetch("""
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as total_executions,
            COUNT(*) FILTER (WHERE success = true) as successful_executions,
            AVG(execution_time_ms) as avg_execution_time_ms,
            SUM(execution_time_ms) as total_execution_time_ms
        FROM mcp_tool_usage
        WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    """, days)

    usage_history = []
    for row in rows:
        usage_history.append({
            "date": row['date'].isoformat(),
            "total_executions": row['total_executions'],
            "successful_executions": row['successful_executions'],
            "success_rate": round(
                (row['successful_executions'] / row['total_executions'] * 100)
                if row['total_executions'] > 0 else 0, 2
            ),
            "avg_execution_time_ms": round(row['avg_execution_time_ms'] or 0, 2),
            "total_execution_time_ms": row['total_execution_time_ms'] or 0
        })

    return usage_history


@router.get("/executions")
async def get_mcp_executions(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    limit: int = Query(50, description="Maximum number of executions to return", ge=1, le=200),
    offset: int = Query(0, description="Number of executions to skip", ge=0)
):
    """Get recent MCP tool executions (filtered by user permissions)"""

    # Users can only see their own executions, admins can see all
    if current_user.role.value in ['parent', 'grandparent']:
        user_filter = ""
    else:
        user_filter = "AND mu.user_id = $1"
        params = [current_user.id, limit, offset]
    else:
        user_filter = "AND mu.user_id = $1"
        params = [current_user.id, limit, offset]

    query = f"""
        SELECT
            mu.execution_id,
            mu.tool_name,
            mu.server_name,
            mu.success,
            mu.result,
            mu.error_message,
            mu.execution_time_ms,
            mu.timestamp,
            fm.first_name,
            fm.last_name,
            fm.role as user_role
        FROM mcp_tool_usage mu
        JOIN family_members fm ON mu.user_id = fm.id
        WHERE TRUE {user_filter}
        ORDER BY mu.timestamp DESC
        LIMIT $2 OFFSET $3
    """

    if current_user.role.value in ['parent', 'grandparent']:
        rows = await db_pool.fetch(query, limit, offset)
    else:
        rows = await db_pool.fetch(query, *params)

    executions = []
    for row in rows:
        executions.append({
            "execution_id": row['execution_id'],
            "tool_name": row['tool_name'],
            "server_name": row['server_name'],
            "success": row['success'],
            "result": row['result'],
            "error_message": row['error_message'],
            "execution_time_ms": row['execution_time_ms'],
            "timestamp": row['timestamp'].isoformat(),
            "user": {
                "first_name": row['first_name'],
                "last_name": row['last_name'],
                "role": row['user_role']
            }
        })

    return executions


# ============================================================================
# MCP Configuration and Health Endpoints
# ============================================================================

@router.get("/health")
async def mcp_health_check(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    mcp_manager: MCPServerManager = Depends(get_mcp_manager)
):
    """Perform health check on all MCP servers"""

    health_status = {}

    for server_name, server in mcp_manager.servers.items():
        # Basic health check - if process is running, consider healthy
        is_healthy = (
            server.status == MCPServerStatus.ONLINE and
            server_name in mcp_manager.running_processes
        )

        health_status[server_name] = {
            "status": server.status.value,
            "healthy": is_healthy,
            "pid": server.pid,
            "last_health_check": server.last_health_check.isoformat() if server.last_health_check else None,
            "error_message": server.error_message,
            "tools_count": len(server.tools)
        }

    return {
        "overall_healthy": all(status["healthy"] for status in health_status.values()),
        "servers": health_status,
        "total_servers": len(health_status),
        "healthy_servers": sum(1 for status in health_status.values() if status["healthy"])
    }