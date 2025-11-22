"""
Admin MCP API Routes

System-wide MCP configuration for Family Assistant administrators.
Manages arcade.dev integration, global tool configuration, and permissions.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import get_current_admin_user, get_db_pool
from api.models.user_management import FamilyMember
from api.services.admin_mcp_manager import AdminMCPManager, SystemMCPServer
import asyncpg


router = APIRouter(prefix="/api/v1/admin/mcp", tags=["Admin MCP"])


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ArcadeDevConfig(BaseModel):
    """Model for arcade.dev configuration"""
    api_token: str = Field(..., description="Arcade.dev API token")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    auto_sync: bool = Field(False, description="Automatically sync servers")

class CustomServerCreate(BaseModel):
    """Model for creating custom MCP server"""
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    connection_type: str = Field(..., description="Connection type: local, remote, etc.")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    allowed_roles: List[str] = Field(default=["parent", "grandparent", "teenager", "child"])

class ToolPermissionUpdate(BaseModel):
    """Model for updating tool permissions"""
    tool_name: str
    family_roles: List[str]
    is_enabled: bool = True
    requires_parent_approval: bool = False


# ============================================================================
# Dependencies
# ============================================================================

async def get_admin_mcp_manager(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> AdminMCPManager:
    """Get admin MCP manager instance"""
    from api.services.admin_mcp_manager import create_admin_mcp_manager
    return await create_admin_mcp_manager(db_pool)


# ============================================================================
# Arcade.dev Configuration Endpoints
# ============================================================================

@router.post("/arcade/configure", response_model=Dict[str, Any])
async def configure_arcade_dev(
    config: ArcadeDevConfig,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager)
):
    """Configure arcade.dev integration for the family system"""
    try:
        success = await mcp_manager.configure_arcade_dev(
            api_token=config.api_token,
            webhook_url=config.webhook_url,
            auto_sync=config.auto_sync
        )

        if success:
            sync_result = await mcp_manager.sync_arcade_servers()
            return {
                "message": "Arcade.dev configured successfully",
                "sync_result": sync_result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to configure arcade.dev"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration failed: {str(e)}"
        )


@router.post("/arcade/sync", response_model=Dict[str, Any])
async def sync_arcade_servers(
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager)
):
    """Manually sync arcade.dev servers"""
    try:
        result = await mcp_manager.sync_arcade_servers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.get("/arcade/status", response_model=Dict[str, Any])
async def get_arcade_status(
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get arcade.dev configuration status"""
    try:
        config = await db_pool.fetchrow("""
            SELECT
                is_enabled,
                auto_sync,
                last_sync,
                sync_errors
            FROM admin_arcade_config
            ORDER BY created_at DESC
            LIMIT 1
        """)

        if not config:
            return {
                "configured": False,
                "enabled": False,
                "last_sync": None,
                "sync_errors": []
            }

        return {
            "configured": True,
            "enabled": config["is_enabled"],
            "auto_sync": config["auto_sync"],
            "last_sync": config["last_sync"].isoformat() if config["last_sync"] else None,
            "sync_errors": config["sync_errors"] or []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


# ============================================================================
# MCP Server Management Endpoints
# ============================================================================

@router.get("/servers", response_model=List[SystemMCPServer])
async def list_admin_servers(
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager)
):
    """List all system MCP servers"""
    try:
        servers = await mcp_manager.get_admin_servers()
        return servers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        )


@router.post("/servers/custom", response_model=Dict[str, str])
async def add_custom_server(
    server_data: CustomServerCreate,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager)
):
    """Add a custom MCP server to the system"""
    try:
        server_id = await mcp_manager.add_custom_server(
            name=server_data.name,
            description=server_data.description,
            connection_type=server_data.connection_type,
            connection_config=server_data.connection_config,
            allowed_roles=server_data.allowed_roles
        )

        return {
            "message": "Custom MCP server added successfully",
            "server_id": server_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add server: {str(e)}"
        )


# ============================================================================
# Tool Permission Management
# ============================================================================

@router.get("/tools/available")
async def list_available_tools(
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager),
    role: Optional[str] = Query(None, description="Filter by family role")
):
    """List available tools for a role (or all roles if not specified)"""
    try:
        if role:
            tools = await mcp_manager.get_available_tools_for_role(role)
        else:
            # Get tools for all roles
            all_roles = ["child", "teenager", "member", "parent", "grandparent"]
            all_tools = {}
            for r in all_roles:
                all_tools[r] = await mcp_manager.get_available_tools_for_role(r)

            return all_tools
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.put("/tools/permissions")
async def update_tool_permissions(
    permission_data: ToolPermissionUpdate,
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager)
):
    """Update permissions for a specific tool"""
    try:
        success = await mcp_manager.update_tool_permissions(
            tool_name=permission_data.tool_name,
            family_roles=permission_data.family_roles,
            is_enabled=permission_data.is_enabled,
            requires_parent_approval=permission_data.requires_parent_approval
        )

        if success:
            return {"message": "Tool permissions updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update permissions: {str(e)}"
        )


# ============================================================================
# Analytics and Monitoring
# ============================================================================

@router.get("/analytics/usage")
async def get_system_usage_analytics(
    current_user: FamilyMember = Depends(get_current_admin_user),
    mcp_manager: AdminMCPManager = Depends(get_admin_mcp_manager),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Get system-wide tool usage analytics"""
    try:
        stats = await mcp_manager.get_system_usage_stats(days)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/analytics/by-role")
async def get_usage_by_role(
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """Get tool usage breakdown by family role"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        role_stats = await db_pool.fetch("""
            SELECT
                fm.role,
                COUNT(DISTINCT ftu.user_id) as unique_users,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN ftu.success = true THEN 1 END) as successful_executions,
                AVG(ftu.execution_time_ms) as avg_execution_time
            FROM family_tool_executions ftu
            JOIN family_members fm ON ftu.user_id = fm.id
            WHERE ftu.timestamp >= $1
            GROUP BY fm.role
            ORDER BY total_executions DESC
        """, start_date)

        return {
            "period_days": days,
            "role_stats": [
                {
                    "role": row["role"],
                    "unique_users": row["unique_users"],
                    "total_executions": row["total_executions"],
                    "success_rate": round(
                        (row["successful_executions"] / row["total_executions"] * 100)
                        if row["total_executions"] else 0, 2
                    ),
                    "avg_execution_time_ms": round(row["avg_execution_time"] or 0, 2)
                }
                for row in role_stats
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role analytics: {str(e)}"
        )


# ============================================================================
# System Configuration
# ============================================================================

@router.get("/config/overview")
async def get_system_config_overview(
    current_user: FamilyMember = Depends(get_current_admin_user),
    db_pool: asyncpg.Pool = Depends(get_db_pool)
):
    """Get overview of system MCP configuration"""
    try:
        # Server counts
        server_stats = await db_pool.fetchrow("""
            SELECT
                COUNT(*) as total_servers,
                COUNT(CASE WHEN is_enabled = true THEN 1 END) as enabled_servers,
                COUNT(CASE WHEN connection_type = 'arcade_dev' THEN 1 END) as arcade_servers,
                COUNT(CASE WHEN is_global = true THEN 1 END) as global_servers
            FROM admin_mcp_servers
        """)

        # Tool counts
        tool_stats = await db_pool.fetchrow("""
            SELECT
                COUNT(*) as total_tools,
                COUNT(CASE WHEN is_enabled = true THEN 1 END) as enabled_tools,
                COUNT(CASE WHEN requires_parent_approval = true THEN 1 END) as parent_approval_required,
                COUNT(CASE WHEN personal_data_risk = 'high' THEN 1 END) as high_risk_tools
            FROM system_tool_availability
        """)

        # Arcade.dev status
        arcade_config = await db_pool.fetchrow("""
            SELECT
                is_enabled as configured,
                last_sync,
                auto_sync
            FROM admin_arcade_config
            ORDER BY created_at DESC
            LIMIT 1
        """)

        return {
            "servers": {
                "total": server_stats["total_servers"] or 0,
                "enabled": server_stats["enabled_servers"] or 0,
                "arcade_dev": server_stats["arcade_servers"] or 0,
                "global": server_stats["global_servers"] or 0
            },
            "tools": {
                "total": tool_stats["total_tools"] or 0,
                "enabled": tool_stats["enabled_tools"] or 0,
                "parent_approval_required": tool_stats["parent_approval_required"] or 0,
                "high_risk": tool_stats["high_risk_tools"] or 0
            },
            "arcade_dev": {
                "configured": bool(arcade_config["configured"]) if arcade_config else False,
                "last_sync": arcade_config["last_sync"].isoformat() if arcade_config and arcade_config["last_sync"] else None,
                "auto_sync": arcade_config["auto_sync"] if arcade_config else False
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config overview: {str(e)}"
        )


@router.get("/setup-guide")
async def get_admin_setup_guide():
    """Get setup guide for administrators"""
    return {
        "title": "Family Assistant MCP Setup Guide",
        "description": "Configure MCP tools and services for your family",
        "steps": [
            {
                "step": 1,
                "title": "Configure Arcade.dev Integration",
                "description": "Connect to arcade.dev marketplace for pre-built tools",
                "actions": [
                    "Get arcade.dev API token",
                    "Configure in Family Assistant admin panel",
                    "Test connection and sync servers"
                ],
                "benefits": ["Wide tool selection", "Easy setup", "Pre-configured"]
            },
            {
                "step": 2,
                "title": "Add Custom MCP Servers",
                "description": "Add your own or local MCP servers",
                "actions": [
                    "Set up local MCP server",
                    "Configure connection details",
                    "Test server connectivity"
                ],
                "benefits": ["Full control", "Custom tools", "Privacy"]
            },
            {
                "step": 3,
                "title": "Configure Tool Permissions",
                "description": "Set up role-based access and safety controls",
                "actions": [
                    "Review available tools",
                    "Set minimum family roles",
                    "Configure parental approval requirements"
                ],
                "benefits": ["Family safety", "Age-appropriate access", "Parental control"]
            },
            {
                "step": 4,
                "title": "Test with Family Members",
                "description": "Verify tools work for different family roles",
                "actions": [
                    "Test child access",
                    "Test teenager access",
                    "Test parent/grandparent access"
                ],
                "benefits": ["Verification", "Training", "Feedback"]
            }
        ],
        "supported_categories": [
            "Calendar & Scheduling",
            "Notes & Documentation",
            "Productivity & Tasks",
            "Weather & Information",
            "Education & Learning",
            "Communication",
            "Development & Coding",
            "File Management",
            "Entertainment & Media"
        ],
        "safety_features": [
            "Role-based access control",
            "Parental approval system",
            "Personal data protection",
            "Usage monitoring and analytics",
            "Tool execution logging"
        ]
    }