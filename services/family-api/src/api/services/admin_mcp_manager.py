"""
Admin MCP Manager - System-wide MCP Configuration

Handles global MCP server configuration, arcade.dev integration,
and tool availability for the entire Family Assistant system.
Only accessible by family administrators.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx

import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SystemMCPTool(BaseModel):
    """Represents a system-wide available MCP tool"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: str = Field(default="general", description="Tool category")
    server_id: str = Field(..., description="System MCP server ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    requires_auth: bool = Field(default=False, description="Requires user authentication")
    personal_data_risk: str = Field(default="low", description="Personal data risk: low/medium/high")
    min_role: str = Field(default="child", description="Minimum family role required")


class SystemMCPServer(BaseModel):
    """System-wide MCP server configuration"""
    id: str
    name: str
    description: Optional[str]
    connection_type: str  # "arcade_dev", "local", "remote"
    connection_config: Dict[str, Any]
    is_enabled: bool
    is_global: bool  # Available to all family members
    allowed_roles: List[str]  # Roles that can use this server
    tools: List[SystemMCPTool]
    health_status: str
    last_health_check: Optional[datetime]
    created_at: datetime


class AdminMCPManager:
    """Manages system-wide MCP configuration for Family Assistant"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.arcade_base_url = "https://api.arcade.dev"
        self.global_auth_token: Optional[str] = None

    async def initialize(self):
        """Initialize admin MCP system"""
        await self._create_admin_mcp_tables()
        await self._load_global_config()
        logger.info("Admin MCP Manager initialized")

    async def _create_admin_mcp_tables(self):
        """Create admin MCP configuration tables"""

        # System MCP servers table (admin configured)
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS admin_mcp_servers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) UNIQUE NOT NULL,
                description TEXT,
                connection_type VARCHAR(50) NOT NULL,
                connection_config JSONB NOT NULL,
                is_enabled BOOLEAN DEFAULT true,
                is_global BOOLEAN DEFAULT true,
                allowed_roles JSONB DEFAULT '["parent", "grandparent", "teenager", "child"]',
                tools JSONB DEFAULT '[]',
                health_status VARCHAR(20) DEFAULT 'unknown',
                last_health_check TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Arcade.dev global configuration
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS admin_arcade_config (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                api_token TEXT,
                webhook_url TEXT,
                is_enabled BOOLEAN DEFAULT false,
                auto_sync BOOLEAN DEFAULT false,
                last_sync TIMESTAMPTZ,
                sync_errors JSONB DEFAULT '[]',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # System tool availability (what family members can see)
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS system_tool_availability (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                server_id UUID REFERENCES admin_mcp_servers(id),
                tool_name VARCHAR(200) NOT NULL,
                family_roles JSONB DEFAULT '["parent", "grandparent", "teenager", "child"]',
                is_enabled BOOLEAN DEFAULT true,
                requires_parent_approval BOOLEAN DEFAULT false,
                personal_data_risk VARCHAR(10) DEFAULT 'low',
                usage_limits JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(server_id, tool_name)
            )
        """)

        # Family member tool preferences
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS family_member_tool_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES family_members(id) ON DELETE CASCADE,
                tool_name VARCHAR(200),
                is_enabled BOOLEAN DEFAULT true,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMPTZ,
                personal_settings JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(user_id, tool_name)
            )
        """)

        # Tool usage statistics
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS system_tool_usage_stats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tool_name VARCHAR(200) NOT NULL,
                server_id UUID REFERENCES admin_mcp_servers(id),
                user_id UUID REFERENCES family_members(id),
                execution_time_ms INTEGER,
                success BOOLEAN,
                error_message TEXT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Indexes
        await self.db_pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_admin_mcp_servers_enabled
            ON admin_mcp_servers(is_enabled) WHERE is_enabled = true;

            CREATE INDEX IF NOT EXISTS idx_system_tool_availability_enabled
            ON system_tool_availability(is_enabled) WHERE is_enabled = true;

            CREATE INDEX IF NOT EXISTS idx_system_tool_usage_stats_timestamp
            ON system_tool_usage_stats(timestamp DESC);
        """)

    async def _load_global_config(self):
        """Load global configuration"""
        # Load arcade.dev config
        config = await self.db_pool.fetchrow("""
            SELECT api_token FROM admin_arcade_config
            WHERE is_enabled = true
        """)

        if config:
            self.global_auth_token = config["api_token"]

    async def configure_arcade_dev(
        self,
        api_token: str,
        webhook_url: Optional[str] = None,
        auto_sync: bool = False
    ) -> bool:
        """Configure global arcade.dev integration"""
        try:
            await self.db_pool.execute("""
                INSERT INTO admin_arcade_config (
                    api_token, webhook_url, is_enabled, auto_sync
                ) VALUES ($1, $2, true, $3)
                ON CONFLICT (id)
                DO UPDATE SET
                    api_token = EXCLUDED.api_token,
                    webhook_url = EXCLUDED.webhook_url,
                    auto_sync = EXCLUDED.auto_sync,
                    updated_at = NOW()
            """, api_token, webhook_url, auto_sync)

            self.global_auth_token = api_token

            # Test connection
            success = await self._test_arcade_connection()

            if success:
                await self.sync_arcade_servers()
                return True
            else:
                await self.db_pool.execute("""
                    UPDATE admin_arcade_config
                    SET is_enabled = false
                    WHERE id = (SELECT id FROM admin_arcade_config ORDER BY created_at DESC LIMIT 1)
                """)
                return False

        except Exception as e:
            logger.error(f"Failed to configure arcade.dev: {e}")
            return False

    async def _test_arcade_connection(self) -> bool:
        """Test arcade.dev API connection"""
        if not self.global_auth_token:
            return False

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.arcade_base_url}/health",
                    headers={"Authorization": f"Bearer {self.global_auth_token}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Arcade.dev connection test failed: {e}")
            return False

    async def sync_arcade_servers(self) -> Dict[str, Any]:
        """Sync available servers from arcade.dev"""
        if not self.global_auth_token:
            return {"error": "Arcade.dev not configured"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.arcade_base_url}/mcp/servers",
                    headers={"Authorization": f"Bearer {self.global_auth_token}"}
                )

                if response.status_code != 200:
                    return {"error": f"Arcade.dev API error: {response.status_code}"}

                servers_data = response.json()
                synced_count = 0

                for server in servers_data.get("servers", []):
                    await self._sync_arcade_server(server)
                    synced_count += 1

                # Update last sync time
                await self.db_pool.execute("""
                    UPDATE admin_arcade_config
                    SET last_sync = NOW(), sync_errors = '[]'
                    WHERE is_enabled = true
                """)

                return {
                    "success": True,
                    "synced_servers": synced_count,
                    "total_servers": len(servers_data.get("servers", []))
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to sync arcade.dev servers: {error_msg}")

            # Log error
            await self.db_pool.execute("""
                UPDATE admin_arcade_config
                SET sync_errors = array_append(
                    COALESCE(sync_errors, '{}'),
                    $1::jsonb
                ) WHERE is_enabled = true
            """, json.dumps({"timestamp": datetime.utcnow().isoformat(), "error": error_msg}))

            return {"error": error_msg}

    async def _sync_arcade_server(self, server_data: Dict[str, Any]):
        """Sync individual arcade.dev server"""
        server_name = server_data.get("name")
        arcade_id = server_data.get("id")

        # Create or update server
        await self.db_pool.execute("""
            INSERT INTO admin_mcp_servers (
                id, name, description, connection_type, connection_config, is_enabled, is_global
            ) VALUES ($1, $2, $3, $4, $5, true, true)
            ON CONFLICT (name)
            DO UPDATE SET
                description = EXCLUDED.description,
                connection_config = EXCLUDED.connection_config,
                updated_at = NOW()
        """,
        arcade_id,
        server_name,
        server_data.get("description"),
        "arcade_dev",
        {
            "arcade_id": arcade_id,
            "requires_auth": server_data.get("requires_auth", False),
            "category": server_data.get("category", "general"),
            "source": "arcade_dev"
        }
        )

        # Get server ID
        server_id = await self.db_pool.fetchval(
            "SELECT id FROM admin_mcp_servers WHERE name = $1",
            server_name
        )

        # Sync tools
        for tool_data in server_data.get("tools", []):
            await self._sync_arcade_tool(server_id, tool_data)

    async def _sync_arcade_tool(self, server_id: str, tool_data: Dict[str, Any]):
        """Sync individual arcade.dev tool"""
        tool_name = tool_data.get("name")
        tool_description = tool_data.get("description")
        category = tool_data.get("category", "general")
        personal_data_risk = self._assess_personal_data_risk(tool_data)

        # Determine minimum role based on tool characteristics
        min_role = self._determine_min_role(tool_data, personal_data_risk)

        # Add to system tool availability
        await self.db_pool.execute("""
            INSERT INTO system_tool_availability (
                server_id, tool_name, family_roles, is_enabled,
                personal_data_risk, requires_parent_approval
            ) VALUES ($1, $2, $3, true, $4, $5)
            ON CONFLICT (server_id, tool_name)
            DO UPDATE SET
                family_roles = EXCLUDED.family_roles,
                personal_data_risk = EXCLUDED.personal_data_risk,
                updated_at = NOW()
        """,
            server_id,
            tool_name,
            self._get_allowed_roles(min_role),
            personal_data_risk,
            min_role in ["parent", "grandparent"]
        )

    def _assess_personal_data_risk(self, tool_data: Dict[str, Any]) -> str:
        """Assess personal data access risk"""
        description = tool_data.get("description", "").lower()
        name = tool_data.get("name", "").lower()

        high_risk_keywords = ["personal", "private", "sensitive", "financial", "health"]
        medium_risk_keywords = ["calendar", "notes", "contacts", "messages"]

        if any(keyword in description or keyword in name for keyword in high_risk_keywords):
            return "high"
        elif any(keyword in description or keyword in name for keyword in medium_risk_keywords):
            return "medium"
        else:
            return "low"

    def _determine_min_role(self, tool_data: Dict[str, Any], personal_data_risk: str) -> str:
        """Determine minimum family role for tool access"""
        if personal_data_risk == "high":
            return "parent"
        elif personal_data_risk == "medium":
            return "teenager"
        else:
            return "child"

    def _get_allowed_roles(self, min_role: str) -> List[str]:
        """Get allowed roles based on minimum role"""
        role_hierarchy = {
            "child": ["child", "teenager", "member", "parent", "grandparent"],
            "teenager": ["teenager", "member", "parent", "grandparent"],
            "member": ["member", "parent", "grandparent"],
            "parent": ["parent", "grandparent"],
            "grandparent": ["grandparent"]
        }
        return role_hierarchy.get(min_role, ["parent", "grandparent"])

    async def get_admin_servers(self) -> List[SystemMCPServer]:
        """Get all system MCP servers (admin view)"""
        rows = await self.db_pool.fetch("""
            SELECT * FROM admin_mcp_servers
            ORDER BY created_at DESC
        """)

        servers = []
        for row in rows:
            # Get tool count
            tool_count = await self.db_pool.fetchval(
                "SELECT COUNT(*) FROM system_tool_availability WHERE server_id = $1 AND is_enabled = true",
                row["id"]
            )

            server = SystemMCPServer(
                id=str(row["id"]),
                name=row["name"],
                description=row["description"],
                connection_type=row["connection_type"],
                connection_config=row["connection_config"],
                is_enabled=row["is_enabled"],
                is_global=row["is_global"],
                allowed_roles=row["allowed_roles"],
                tools=[],  # Tools loaded separately
                health_status=row["health_status"],
                last_health_check=row["last_health_check"],
                created_at=row["created_at"]
            )
            servers.append(server)

        return servers

    async def add_custom_server(
        self,
        name: str,
        description: Optional[str],
        connection_type: str,
        connection_config: Dict[str, Any],
        allowed_roles: Optional[List[str]] = None
    ) -> str:
        """Add custom MCP server (admin only)"""
        try:
            server_id = await self.db_pool.fetchval("""
                INSERT INTO admin_mcp_servers (
                    name, description, connection_type, connection_config,
                    is_enabled, is_global, allowed_roles
                ) VALUES ($1, $2, $3, $4, true, true, $5)
                RETURNING id
            """, name, description, connection_type, connection_config,
                allowed_roles or ["parent", "grandparent", "teenager", "child"])

            return str(server_id)
        except Exception as e:
            logger.error(f"Failed to add custom server: {e}")
            raise

    async def get_available_tools_for_role(
        self,
        user_role: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get tools available for a specific family role"""

        # Get base tools available for role
        rows = await self.db_pool.fetch("""
            SELECT
                sta.tool_name,
                sta.family_roles,
                sta.personal_data_risk,
                sta.requires_parent_approval,
                ams.name as server_name,
                ams.connection_type,
                COALESCE(ftmp.usage_count, 0) as usage_count,
                COALESCE(ftmp.is_enabled, true) as user_enabled
            FROM system_tool_availability sta
            JOIN admin_mcp_servers ams ON sta.server_id = ams.id
            LEFT JOIN family_member_tool_preferences ftmp ON
                sta.tool_name = ftmp.tool_name AND ftmp.user_id = $1
            WHERE
                sta.is_enabled = true AND
                ams.is_enabled = true AND
                $2 = ANY(sta.family_roles)
            ORDER BY usage_count DESC, sta.tool_name
        """, user_id or "", user_role)

        tools = []
        for row in rows:
            tools.append({
                "name": row["tool_name"],
                "server_name": row["server_name"],
                "connection_type": row["connection_type"],
                "personal_data_risk": row["personal_data_risk"],
                "requires_parent_approval": row["requires_parent_approval"],
                "usage_count": row["usage_count"],
                "user_enabled": row["user_enabled"],
                "description": f"Tool from {row['server_name']} ({row['connection_type']})"
            })

        return tools

    async def update_tool_permissions(
        self,
        tool_name: str,
        family_roles: List[str],
        is_enabled: bool = True,
        requires_parent_approval: bool = False
    ) -> bool:
        """Update tool permissions (admin only)"""
        try:
            result = await self.db_pool.execute("""
                UPDATE system_tool_availability
                SET
                    family_roles = $2,
                    is_enabled = $3,
                    requires_parent_approval = $4,
                    updated_at = NOW()
                WHERE tool_name = $1
            """, tool_name, family_roles, is_enabled, requires_parent_approval)

            return result == "UPDATE 1"
        except Exception as e:
            logger.error(f"Failed to update tool permissions: {e}")
            return False

    async def get_system_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide tool usage statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)

        stats = await self.db_pool.fetchrow("""
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_executions,
                AVG(execution_time_ms) as avg_execution_time,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT tool_name) as unique_tools
            FROM system_tool_usage_stats
            WHERE timestamp >= $1
        """, start_date)

        # Top tools
        top_tools = await self.db_pool.fetch("""
            SELECT
                tool_name,
                COUNT(*) as usage_count,
                AVG(execution_time_ms) as avg_time_ms,
                COUNT(CASE WHEN success = true THEN 1 END) as success_count
            FROM system_tool_usage_stats
            WHERE timestamp >= $1
            GROUP BY tool_name
            ORDER BY usage_count DESC
            LIMIT 10
        """, start_date)

        # Usage by role
        role_usage = await self.db_pool.fetch("""
            SELECT
                fm.role,
                COUNT(*) as usage_count,
                COUNT(DISTINCT stus.user_id) as unique_users
            FROM system_tool_usage_stats stus
            JOIN family_members fm ON stus.user_id = fm.id
            WHERE stus.timestamp >= $1
            GROUP BY fm.role
            ORDER BY usage_count DESC
        """, start_date)

        return {
            "period_days": days,
            "total_executions": stats["total_executions"] or 0,
            "successful_executions": stats["successful_executions"] or 0,
            "success_rate": round(
                (stats["successful_executions"] / stats["total_executions"] * 100)
                if stats["total_executions"] else 0, 2
            ),
            "avg_execution_time_ms": round(stats["avg_execution_time"] or 0, 2),
            "unique_users": stats["unique_users"] or 0,
            "unique_tools": stats["unique_tools"] or 0,
            "top_tools": [
                {
                    "tool_name": row["tool_name"],
                    "usage_count": row["usage_count"],
                    "success_rate": round(
                        (row["success_count"] / row["usage_count"] * 100)
                        if row["usage_count"] else 0, 2
                    ),
                    "avg_time_ms": round(row["avg_time_ms"] or 0, 2)
                }
                for row in top_tools
            ],
            "role_usage": [
                {
                    "role": row["role"],
                    "usage_count": row["usage_count"],
                    "unique_users": row["unique_users"]
                }
                for row in role_usage
            ]
        }


# ============================================================================
# Factory Functions
# ============================================================================

async def create_admin_mcp_manager(db_pool: asyncpg.Pool) -> AdminMCPManager:
    """Create admin MCP manager instance"""
    manager = AdminMCPManager(db_pool)
    await manager.initialize()
    return manager