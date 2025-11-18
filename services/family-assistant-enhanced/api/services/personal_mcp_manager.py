"""
Personal MCP Manager - User-Facing Tool Extension System

Allows Family Assistant users to connect their personal MCP servers
and tools to extend the assistant's capabilities.

Integration with:
- arcade.dev for MCP server discovery and management
- User's personal MCP tools (calendar, notes, personal services)
- Family context and safety controls
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
from enum import Enum
import uuid
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlparse

import asyncpg
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)


class PersonalMCPServerStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"
    DISABLED = "disabled"


class PersonalMCPTool(BaseModel):
    """Represents a personal MCP tool from user's server"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_name: str = Field(..., description="User's MCP server name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    category: str = Field(default="general", description="Tool category: calendar, notes, productivity, etc.")
    personal_data_access: bool = Field(default=False, description="Can access personal data")
    safety_level: str = Field(default="medium", description="Safety level: low/medium/high")
    requires_auth: bool = Field(default=False, description="Requires user authentication")


class PersonalMCPServer(BaseModel):
    """Represents a user's personal MCP server"""
    id: str = Field(..., description="Unique server ID")
    user_id: str = Field(..., description="Family member ID")
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(None, description="Server description")
    connection_type: str = Field(..., description="Connection type: arcade, local, remote")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    status: PersonalMCPServerStatus = Field(default=PersonalMCPServerStatus.DISCONNECTED)
    tools: List[PersonalMCPTool] = Field(default_factory=list, description="Available tools")
    last_connected: Optional[datetime] = Field(None, description="Last successful connection")
    error_message: Optional[str] = Field(None, description="Last error message")
    is_active: bool = Field(default=True, description="Server is enabled for use")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArcadeDevIntegration:
    """Integration with arcade.dev for MCP server management"""

    def __init__(self):
        self.base_url = "https://api.arcade.dev"
        self.timeout = 30

    async def discover_mcp_servers(self, user_token: str) -> List[Dict[str, Any]]:
        """Discover user's MCP servers from arcade.dev"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/mcp/servers",
                    headers={"Authorization": f"Bearer {user_token}"}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Arcade.dev API error: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Failed to discover MCP servers from arcade.dev: {e}")
            return []

    async def get_mcp_server_details(self, user_token: str, server_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific MCP server"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/mcp/servers/{server_id}",
                    headers={"Authorization": f"Bearer {user_token}"}
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to get MCP server details: {e}")
            return None

    async def connect_mcp_server(self, user_token: str, server_id: str, connection_config: Dict[str, Any]) -> Dict[str, Any]:
        """Establish connection to MCP server via arcade.dev"""

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/mcp/servers/{server_id}/connect",
                    headers={"Authorization": f"Bearer {user_token}"},
                    json=connection_config
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Connection failed: {response.status_code}"}

        except Exception as e:
            logger.error(f"Failed to connect MCP server: {e}")
            return {"error": str(e)}


class PersonalMCPManager:
    """Manages personal MCP servers for Family Assistant users"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.arcade_integration = ArcadeDevIntegration()
        self.active_connections: Dict[str, Any] = {}  # user_id -> connections

    async def initialize(self):
        """Initialize personal MCP system"""
        await self._create_personal_mcp_tables()
        logger.info("Personal MCP Manager initialized")

    async def _create_personal_mcp_tables(self):
        """Create personal MCP-related database tables"""

        # Personal MCP servers table
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS personal_mcp_servers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                connection_type VARCHAR(50) NOT NULL,
                connection_config JSONB NOT NULL,
                status VARCHAR(20) DEFAULT 'disconnected',
                tools JSONB DEFAULT '[]',
                last_connected TIMESTAMPTZ,
                error_message TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(user_id, name)
            )
        """)

        # Personal MCP tool usage logs
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS personal_mcp_tool_usage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                execution_id VARCHAR(100) NOT NULL,
                user_id UUID NOT NULL REFERENCES family_members(id),
                server_id UUID REFERENCES personal_mcp_servers(id),
                tool_name VARCHAR(200) NOT NULL,
                parameters JSONB DEFAULT '{}',
                success BOOLEAN NOT NULL,
                result JSONB,
                error_message TEXT,
                execution_time_ms INTEGER,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                personal_data_accessed BOOLEAN DEFAULT false
            )
        """)

        # Personal MCP server connections table (for authentication tokens)
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS personal_mcp_connections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                platform VARCHAR(50) NOT NULL,
                auth_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(user_id, platform)
            )
        """)

        # Create indexes
        await self.db_pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_personal_mcp_servers_user_id
            ON personal_mcp_servers(user_id);

            CREATE INDEX IF NOT EXISTS idx_personal_mcp_usage_user_timestamp
            ON personal_mcp_tool_usage(user_id, timestamp DESC);
        """)

    async def discover_arcade_servers(self, user_id: str) -> List[Dict[str, Any]]:
        """Discover MCP servers from arcade.dev for a user"""

        # Get user's arcade.dev auth token
        auth_token = await self._get_user_auth_token(user_id, "arcade")

        if not auth_token:
            logger.warning(f"No arcade.dev token found for user {user_id}")
            return []

        # Discover servers from arcade.dev
        servers = await self.arcade_integration.discover_mcp_servers(auth_token)

        # Format for frontend
        discovered_servers = []
        for server in servers:
            discovered_servers.append({
                "id": server.get("id"),
                "name": server.get("name"),
                "description": server.get("description"),
                "category": server.get("category", "general"),
                "tool_count": len(server.get("tools", [])),
                "requires_auth": server.get("requires_auth", False),
                "source": "arcade_dev"
            })

        return discovered_servers

    async def connect_arcade_server(
        self,
        user_id: str,
        arcade_server_id: str,
        server_name: str,
        description: Optional[str] = None
    ) -> str:
        """Connect to an arcade.dev MCP server for the user"""

        # Get user's arcade.dev auth token
        auth_token = await self._get_user_auth_token(user_id, "arcade")

        if not auth_token:
            raise ValueError("No arcade.dev authentication token found")

        # Get server details from arcade.dev
        server_details = await self.arcade_integration.get_mcp_server_details(auth_token, arcade_server_id)

        if not server_details:
            raise ValueError(f"Server {arcade_server_id} not found on arcade.dev")

        # Create connection configuration
        connection_config = {
            "arcade_server_id": arcade_server_id,
            "auth_required": server_details.get("requires_auth", False),
            "connection_type": "arcade",
            "server_info": server_details
        }

        # Create personal MCP server record
        server_id = await self.db_pool.fetchval("""
            INSERT INTO personal_mcp_servers (
                user_id, name, description, connection_type, connection_config
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, user_id, server_name, description, "arcade", connection_config)

        # Discover tools from the server
        await self._discover_tools_from_server(server_id, server_details)

        return server_id

    async def add_local_mcp_server(
        self,
        user_id: str,
        name: str,
        command: str,
        args: List[str],
        description: Optional[str] = None
    ) -> str:
        """Add a local MCP server for the user"""

        connection_config = {
            "command": command,
            "args": args,
            "type": "local",
            "working_directory": str(Path.home())
        }

        server_id = await self.db_pool.fetchval("""
            INSERT INTO personal_mcp_servers (
                user_id, name, description, connection_type, connection_config
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
        """, user_id, name, description, "local", connection_config)

        return server_id

    async def _discover_tools_from_server(self, server_id: str, server_details: Dict[str, Any]):
        """Discover and store tools from a server"""

        tools = []
        for tool_data in server_details.get("tools", []):
            tool = PersonalMCPTool(
                name=tool_data.get("name"),
                description=tool_data.get("description"),
                server_name=tool_data.get("server_name"),
                parameters=tool_data.get("parameters", {}),
                category=tool_data.get("category", "general"),
                personal_data_access=tool_data.get("personal_data_access", False),
                safety_level=tool_data.get("safety_level", "medium"),
                requires_auth=tool_data.get("requires_auth", False)
            )
            tools.append(tool.dict())

        # Update server with discovered tools
        await self.db_pool.execute("""
            UPDATE personal_mcp_servers
            SET tools = $2, updated_at = NOW()
            WHERE id = $1
        """, server_id, tools)

    async def get_user_servers(self, user_id: str) -> List[PersonalMCPServer]:
        """Get all personal MCP servers for a user"""

        rows = await self.db_pool.fetch("""
            SELECT * FROM personal_mcp_servers
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
        """, user_id)

        servers = []
        for row in rows:
            server = PersonalMCPServer(
                id=str(row["id"]),
                user_id=row["user_id"],
                name=row["name"],
                description=row["description"],
                connection_type=row["connection_type"],
                connection_config=row["connection_config"],
                status=PersonalMCPServerStatus(row["status"]),
                tools=[PersonalMCPTool(**tool) for tool in (row["tools"] or [])],
                last_connected=row["last_connected"],
                error_message=row["error_message"],
                is_active=row["is_active"],
                created_at=row["created_at"]
            )
            servers.append(server)

        return servers

    async def execute_personal_tool(
        self,
        user_id: str,
        server_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a personal MCP tool"""

        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            # Get server details
            server = await self.db_pool.fetchrow("""
                SELECT * FROM personal_mcp_servers
                WHERE id = $1 AND user_id = $2 AND is_active = true
            """, server_id, user_id)

            if not server:
                return {
                    "success": False,
                    "error": "Server not found or inactive",
                    "execution_id": execution_id
                }

            # Check if tool exists
            tools = server["tools"] or []
            tool = next((t for t in tools if t["name"] == tool_name), None)

            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found on server",
                    "execution_id": execution_id
                }

            # Execute tool based on connection type
            if server["connection_type"] == "arcade":
                result = await self._execute_arcade_tool(
                    user_id, server, tool, parameters
                )
            elif server["connection_type"] == "local":
                result = await self._execute_local_tool(
                    user_id, server, tool, parameters
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported connection type: {server['connection_type']}"
                }

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Log execution
            await self._log_tool_execution(
                execution_id, user_id, server_id, tool_name, parameters,
                result.get("success", False), result.get("result"), result.get("error"),
                execution_time, tool.get("personal_data_access", False)
            )

            # Update server last connected time
            if result.get("success"):
                await self.db_pool.execute("""
                    UPDATE personal_mcp_servers
                    SET last_connected = NOW(), status = 'connected', error_message = NULL
                    WHERE id = $1
                """, server_id)

            return {
                "execution_id": execution_id,
                "execution_time_ms": execution_time,
                **result
            }

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Log error
            await self._log_tool_execution(
                execution_id, user_id, server_id, tool_name, parameters,
                False, None, str(e), execution_time, False
            )

            return {
                "execution_id": execution_id,
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }

    async def _execute_arcade_tool(
        self,
        user_id: str,
        server: Dict[str, Any],
        tool: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool via arcade.dev"""

        try:
            # Get user's arcade.dev auth token
            auth_token = await self._get_user_auth_token(user_id, "arcade")

            if not auth_token:
                return {
                    "success": False,
                    "error": "No arcade.dev authentication token"
                }

            connection_config = server["connection_config"]
            arcade_server_id = connection_config["arcade_server_id"]

            # Execute via arcade.dev API
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.arcade_integration.base_url}/mcp/servers/{arcade_server_id}/tools/{tool['name']}/execute",
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={
                        "parameters": parameters,
                        "context": {
                            "family_assistant": True,
                            "user_id": user_id
                        }
                    }
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "result": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Arcade.dev API error: {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Arcade.dev execution failed: {str(e)}"
            }

    async def _execute_local_tool(
        self,
        user_id: str,
        server: Dict[str, Any],
        tool: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool from local MCP server"""

        try:
            connection_config = server["connection_config"]
            command = connection_config["command"]
            args = connection_config.get("args", [])

            # This is a simplified implementation
            # In a real implementation, you would use the MCP protocol
            # to communicate with the local server

            # Mock execution for now
            await asyncio.sleep(1)  # Simulate tool execution time

            result = {
                "tool_name": tool["name"],
                "parameters": parameters,
                "message": f"Tool '{tool['name']}' executed successfully",
                "data": {"mock": True, "local": True}
            }

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Local tool execution failed: {str(e)}"
            }

    async def _log_tool_execution(
        self,
        execution_id: str,
        user_id: str,
        server_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        success: bool,
        result: Optional[Any],
        error: Optional[str],
        execution_time_ms: int,
        personal_data_accessed: bool
    ):
        """Log tool execution for analytics"""

        await self.db_pool.execute("""
            INSERT INTO personal_mcp_tool_usage (
                execution_id, user_id, server_id, tool_name, parameters,
                success, result, error_message, execution_time_ms, personal_data_accessed
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, execution_id, user_id, server_id, tool_name, parameters,
              success, result, error, execution_time_ms, personal_data_accessed)

    async def _get_user_auth_token(self, user_id: str, platform: str) -> Optional[str]:
        """Get user's auth token for a platform"""

        token = await self.db_pool.fetchval("""
            SELECT auth_token FROM personal_mcp_connections
            WHERE user_id = $1 AND platform = $2 AND is_active = true
            AND (expires_at IS NULL OR expires_at > NOW())
        """, user_id, platform)

        return token

    async def store_auth_token(
        self,
        user_id: str,
        platform: str,
        auth_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ):
        """Store user's auth token for a platform"""

        await self.db_pool.execute("""
            INSERT INTO personal_mcp_connections (
                user_id, platform, auth_token, refresh_token, expires_at
            ) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, platform)
            DO UPDATE SET
                auth_token = EXCLUDED.auth_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
        """, user_id, platform, auth_token, refresh_token, expires_at)

    async def get_tool_usage_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get tool usage statistics for a user"""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Overall stats
        stats = await self.db_pool.fetchrow("""
            SELECT
                COUNT(*) as total_executions,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_executions,
                AVG(execution_time_ms) as avg_execution_time,
                COUNT(DISTINCT server_id) as unique_servers_used,
                COUNT(DISTINCT tool_name) as unique_tools_used
            FROM personal_mcp_tool_usage
            WHERE user_id = $1 AND timestamp >= $2
        """, user_id, start_date)

        # Most used tools
        top_tools = await self.db_pool.fetch("""
            SELECT
                tool_name,
                COUNT(*) as usage_count,
                COUNT(CASE WHEN success = true THEN 1 END) as success_count
            FROM personal_mcp_tool_usage
            WHERE user_id = $1 AND timestamp >= $2
            GROUP BY tool_name
            ORDER BY usage_count DESC
            LIMIT 10
        """, user_id, start_date)

        # Server usage
        server_usage = await self.db_pool.fetch("""
            SELECT
                ps.name as server_name,
                COUNT(*) as usage_count,
                COUNT(CASE WHEN success = true THEN 1 END) as success_count
            FROM personal_mcp_tool_usage ptu
            JOIN personal_mcp_servers ps ON ptu.server_id = ps.id
            WHERE ptu.user_id = $1 AND ptu.timestamp >= $2
            GROUP BY ps.id, ps.name
            ORDER BY usage_count DESC
        """, user_id, start_date)

        return {
            "period_days": days,
            "total_executions": stats["total_executions"] or 0,
            "successful_executions": stats["successful_executions"] or 0,
            "success_rate": round(
                (stats["successful_executions"] / stats["total_executions"] * 100)
                if stats["total_executions"] else 0, 2
            ),
            "avg_execution_time_ms": round(stats["avg_execution_time"] or 0, 2),
            "unique_servers_used": stats["unique_servers_used"] or 0,
            "unique_tools_used": stats["unique_tools_used"] or 0,
            "top_tools": [
                {
                    "tool_name": row["tool_name"],
                    "usage_count": row["usage_count"],
                    "success_rate": round(
                        (row["success_count"] / row["usage_count"] * 100)
                        if row["usage_count"] else 0, 2
                    )
                }
                for row in top_tools
            ],
            "server_usage": [
                {
                    "server_name": row["server_name"],
                    "usage_count": row["usage_count"],
                    "success_rate": round(
                        (row["success_count"] / row["usage_count"] * 100)
                        if row["usage_count"] else 0, 2
                    )
                }
                for row in server_usage
            ]
        }

    async def disconnect_server(self, user_id: str, server_id: str) -> bool:
        """Disconnect a personal MCP server"""

        # Mark server as inactive
        result = await self.db_pool.execute("""
            UPDATE personal_mcp_servers
            SET is_active = false, status = 'disconnected', updated_at = NOW()
            WHERE id = $1 AND user_id = $2
        """, server_id, user_id)

        return result == "UPDATE 1"


# ============================================================================
# Factory Functions
# ============================================================================

async def create_personal_mcp_manager(db_pool: asyncpg.Pool) -> PersonalMCPManager:
    """Create personal MCP manager instance"""
    manager = PersonalMCPManager(db_pool)
    await manager.initialize()
    return manager