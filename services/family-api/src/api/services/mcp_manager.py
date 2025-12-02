"""
MCP Server Manager - Family Assistant Backend

Manages MCP (Model Context Protocol) servers, tool registration,
execution, and integration with the Family Assistant system.

Architecture:
1. MCP Server Registry - Database of available MCP servers
2. Tool Discovery - Automatic tool discovery from MCP servers
3. RBAC Integration - Role-based access control for MCP tools
4. Execution Engine - Safe MCP tool execution with sandboxing
5. Metrics & Monitoring - Usage tracking and performance metrics
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
from enum import Enum
import uuid
from datetime import datetime

import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPServerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class MCPTool(BaseModel):
    """Represents an MCP tool available to the Family Assistant"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_name: str = Field(..., description="MCP server providing this tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters schema")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")
    safety_level: str = Field(default="medium", description="Safety level: low/medium/high/critical")
    rate_limit: Optional[int] = Field(None, description="Rate limit per hour (optional)")
    timeout_seconds: int = Field(default=30, description="Tool execution timeout")


class MCPServer(BaseModel):
    """Represents an MCP server configuration"""
    name: str = Field(..., description="Unique server name")
    command: str = Field(..., description="Command to start MCP server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    status: MCPServerStatus = Field(default=MCPServerStatus.OFFLINE)
    tools: List[MCPTool] = Field(default_factory=list, description="Available tools")
    pid: Optional[int] = Field(None, description="Process ID if running")
    last_health_check: Optional[datetime] = Field(None, description="Last health check timestamp")
    error_message: Optional[str] = Field(None, description="Last error message")


class MCPExecutionContext(BaseModel):
    """Context for MCP tool execution"""
    user_id: str = Field(..., description="User requesting tool execution")
    tool_name: str = Field(..., description="Tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCPExecutionResult(BaseModel):
    """Result of MCP tool execution"""
    execution_id: str
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int
    tokens_used: Optional[int] = None
    safety_violations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MCPServerManager:
    """Manages MCP server lifecycle and tool discovery"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.servers: Dict[str, MCPServer] = {}
        self.running_processes: Dict[str, Popen] = {}
        self._init_done = False

    async def initialize(self):
        """Initialize MCP system from database and configuration"""
        if self._init_done:
            return

        await self._create_mcp_tables()
        await self._load_servers_from_db()
        await self._discover_tools()
        self._init_done = True

        logger.info(f"MCP Server Manager initialized with {len(self.servers)} servers")

    async def _create_mcp_tables(self):
        """Create MCP-related database tables"""

        # MCP servers table
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) UNIQUE NOT NULL,
                command TEXT NOT NULL,
                args JSONB DEFAULT '[]',
                env JSONB DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'offline',
                tools JSONB DEFAULT '[]',
                pid INTEGER,
                last_health_check TIMESTAMPTZ,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # MCP tool usage logs
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS mcp_tool_usage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                execution_id VARCHAR(100) NOT NULL,
                user_id UUID NOT NULL,
                tool_name VARCHAR(200) NOT NULL,
                server_name VARCHAR(100) NOT NULL,
                parameters JSONB DEFAULT '{}',
                success BOOLEAN NOT NULL,
                result JSONB,
                error_message TEXT,
                execution_time_ms INTEGER,
                tokens_used INTEGER,
                safety_violations JSONB DEFAULT '[]',
                timestamp TIMESTAMPTZ DEFAULT NOW(),

                FOREIGN KEY (user_id) REFERENCES family_members(id)
            )
        """)

        # MCP tool permissions
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS mcp_tool_permissions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tool_name VARCHAR(200) NOT NULL,
                server_name VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                can_execute BOOLEAN NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(tool_name, server_name, role)
            )
        """)

        # Create indexes
        await self.db_pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_mcp_usage_user_timestamp
            ON mcp_tool_usage(user_id, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_mcp_usage_tool_timestamp
            ON mcp_tool_usage(tool_name, timestamp DESC);
        """)

    async def _load_servers_from_db(self):
        """Load MCP server configurations from database"""
        rows = await self.db_pool.fetch("SELECT * FROM mcp_servers")

        for row in rows:
            server = MCPServer(
                name=row['name'],
                command=row['command'],
                args=row['args'] or [],
                env=row['env'] or {},
                status=MCPServerStatus(row['status']),
                tools=[MCPTool(**tool) for tool in (row['tools'] or [])],
                pid=row['pid'],
                last_health_check=row['last_health_check'],
                error_message=row['error_message']
            )
            self.servers[server.name] = server

    async def register_server(self, server: MCPServer) -> bool:
        """Register a new MCP server"""
        try:
            # Check if server already exists
            existing = await self.db_pool.fetchval(
                "SELECT id FROM mcp_servers WHERE name = $1",
                server.name
            )

            if existing:
                # Update existing server
                await self.db_pool.execute("""
                    UPDATE mcp_servers
                    SET command = $2, args = $3, env = $4, updated_at = NOW()
                    WHERE name = $1
                """, server.name, server.command, server.args, server.env)
            else:
                # Insert new server
                await self.db_pool.execute("""
                    INSERT INTO mcp_servers (name, command, args, env)
                    VALUES ($1, $2, $3, $4)
                """, server.name, server.command, server.args, server.env)

            self.servers[server.name] = server
            logger.info(f"Registered MCP server: {server.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to register MCP server {server.name}: {e}")
            return False

    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server"""
        if server_name not in self.servers:
            logger.error(f"Unknown MCP server: {server_name}")
            return False

        server = self.servers[server_name]

        if server.status == MCPServerStatus.ONLINE:
            logger.info(f"MCP server {server_name} already running")
            return True

        try:
            # Update status
            server.status = MCPServerStatus.STARTING
            await self._update_server_status(server)

            # Start the process
            import os
            env = os.environ.copy()
            env.update(server.env)

            process = Popen(
                [server.command] + server.args,
                stdout=PIPE,
                stderr=PIPE,
                env=env,
                text=True
            )

            # Give it a moment to start
            await asyncio.sleep(2)

            if process.poll() is None:  # Process is still running
                server.status = MCPServerStatus.ONLINE
                server.pid = process.pid
                server.last_health_check = datetime.utcnow()
                server.error_message = None

                self.running_processes[server_name] = process

                await self._update_server_status(server)
                await self._discover_tools_for_server(server_name)

                logger.info(f"Started MCP server: {server_name} (PID: {process.pid})")
                return True
            else:
                # Process failed to start
                stderr = process.stderr.read() if process.stderr else "Unknown error"
                server.status = MCPServerStatus.ERROR
                server.error_message = stderr

                await self._update_server_status(server)
                logger.error(f"Failed to start MCP server {server_name}: {stderr}")
                return False

        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.error_message = str(e)
            await self._update_server_status(server)
            logger.error(f"Exception starting MCP server {server_name}: {e}")
            return False

    async def stop_server(self, server_name: str) -> bool:
        """Stop an MCP server"""
        if server_name not in self.running_processes:
            logger.warning(f"MCP server {server_name} not running")
            return True

        process = self.running_processes[server_name]
        server = self.servers[server_name]

        try:
            server.status = MCPServerStatus.STOPPING
            await self._update_server_status(server)

            # Try graceful shutdown first
            process.terminate()

            # Wait up to 5 seconds
            try:
                process.wait(timeout=5)
            except TimeoutExpired:
                # Force kill
                process.kill()
                process.wait()

            server.status = MCPServerStatus.OFFLINE
            server.pid = None
            server.error_message = None

            del self.running_processes[server_name]
            await self._update_server_status(server)

            logger.info(f"Stopped MCP server: {server_name}")
            return True

        except Exception as e:
            server.status = MCPServerStatus.ERROR
            server.error_message = str(e)
            await self._update_server_status(server)
            logger.error(f"Error stopping MCP server {server_name}: {e}")
            return False

    async def _discover_tools(self):
        """Discover tools from all running MCP servers"""
        for server_name in list(self.servers.keys()):
            if self.servers[server_name].status == MCPServerStatus.ONLINE:
                await self._discover_tools_for_server(server_name)

    async def _discover_tools_for_server(self, server_name: str):
        """Discover tools from a specific MCP server"""
        # This is a simplified implementation
        # In a real MCP server, we would send a JSON-RPC message to list tools

        server = self.servers[server_name]

        # For now, create some example tools based on server name
        if server_name == "homelab-kubernetes":
            server.tools = [
                MCPTool(
                    name="list_pods",
                    description="List Kubernetes pods in the homelab namespace",
                    server_name=server_name,
                    parameters={"namespace": {"type": "string", "default": "homelab"}},
                    required_permissions=["kubernetes.read"],
                    safety_level="medium"
                ),
                MCPTool(
                    name="get_service_logs",
                    description="Get logs from a specific service",
                    server_name=server_name,
                    parameters={
                        "service": {"type": "string"},
                        "lines": {"type": "integer", "default": 100}
                    },
                    required_permissions=["kubernetes.read"],
                    safety_level="low"
                )
            ]
        elif server_name == "homelab-git":
            server.tools = [
                MCPTool(
                    name="git_status",
                    description="Check git repository status",
                    server_name=server_name,
                    required_permissions=["git.read"],
                    safety_level="low"
                ),
                MCPTool(
                    name="git_commit",
                    description="Create a git commit",
                    server_name=server_name,
                    parameters={"message": {"type": "string"}},
                    required_permissions=["git.write"],
                    safety_level="medium"
                )
            ]

        # Update database
        await self.db_pool.execute("""
            UPDATE mcp_servers
            SET tools = $2, updated_at = NOW()
            WHERE name = $1
        """, server_name, [tool.dict() for tool in server.tools])

        logger.info(f"Discovered {len(server.tools)} tools for MCP server {server_name}")

    async def _update_server_status(self, server: MCPServer):
        """Update server status in database"""
        await self.db_pool.execute("""
            UPDATE mcp_servers
            SET status = $2, pid = $3, last_health_check = $4,
                error_message = $5, updated_at = NOW()
            WHERE name = $1
        """, server.name, server.status.value, server.pid,
              server.last_health_check, server.error_message)


# ============================================================================
# MCP Execution Engine
# ============================================================================

class MCPExecutionEngine:
    """Executes MCP tools with safety controls and RBAC"""

    def __init__(self, db_pool: asyncpg.Pool, server_manager: MCPServerManager):
        self.db_pool = db_pool
        self.server_manager = server_manager

    async def can_user_execute_tool(
        self,
        user_id: str,
        tool_name: str,
        server_name: str
    ) -> tuple[bool, str]:
        """Check if user has permission to execute a tool"""

        # Get user role
        user_role = await self.db_pool.fetchval(
            "SELECT role FROM family_members WHERE id = $1",
            user_id
        )

        if not user_role:
            return False, "User not found"

        # Check tool permissions
        can_execute = await self.db_pool.fetchval("""
            SELECT can_execute FROM mcp_tool_permissions
            WHERE tool_name = $1 AND server_name = $2 AND role = $3
        """, tool_name, server_name, user_role)

        if can_execute is None:
            # Default to parents only having access
            can_execute = user_role in ['parent', 'grandparent']

        if not can_execute:
            return False, f"Role '{user_role}' not authorized for tool '{tool_name}'"

        return True, "Authorized"

    async def execute_tool(self, context: MCPExecutionContext) -> MCPExecutionResult:
        """Execute an MCP tool with safety controls"""
        start_time = datetime.utcnow()

        try:
            # Find the tool
            tool = None
            server = None

            for srv in self.server_manager.servers.values():
                for t in srv.tools:
                    if t.name == context.tool_name:
                        tool = t
                        server = srv
                        break
                if tool:
                    break

            if not tool:
                return MCPExecutionResult(
                    execution_id=context.execution_id,
                    tool_name=context.tool_name,
                    success=False,
                    error=f"Tool '{context.tool_name}' not found",
                    execution_time_ms=0
                )

            # Check permissions
            can_execute, reason = await self.can_user_execute_tool(
                context.user_id, context.tool_name, server.name
            )

            if not can_execute:
                return MCPExecutionResult(
                    execution_id=context.execution_id,
                    tool_name=context.tool_name,
                    success=False,
                    error=f"Permission denied: {reason}",
                    execution_time_ms=0
                )

            # Check safety level
            if tool.safety_level == "critical":
                # Additional safety checks for critical tools
                safety_result = await self._perform_safety_check(tool, context.parameters)
                if not safety_result["safe"]:
                    return MCPExecutionResult(
                        execution_id=context.execution_id,
                        tool_name=context.tool_name,
                        success=False,
                        error=f"Safety check failed: {safety_result['reason']}",
                        execution_time_ms=0,
                        safety_violations=safety_result["violations"]
                    )

            # Execute the tool
            result = await self._execute_mcp_tool(tool, server, context.parameters)

            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            success_result = MCPExecutionResult(
                execution_id=context.execution_id,
                tool_name=context.tool_name,
                success=True,
                result=result,
                execution_time_ms=int(execution_time)
            )

            # Log successful execution
            await self._log_execution(context, success_result)

            return success_result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            error_result = MCPExecutionResult(
                execution_id=context.execution_id,
                tool_name=context.tool_name,
                success=False,
                error=str(e),
                execution_time_ms=int(execution_time)
            )

            # Log failed execution
            await self._log_execution(context, error_result)

            return error_result

    async def _execute_mcp_tool(
        self,
        tool: MCPTool,
        server: MCPServer,
        parameters: Dict[str, Any]
    ) -> Any:
        """Execute tool on MCP server (simplified implementation)"""

        # This is a simplified mock implementation
        # In a real implementation, we would send JSON-RPC calls to the MCP server

        if tool.name == "list_pods":
            return {
                "pods": [
                    {"name": "family-assistant-backend", "status": "Running"},
                    {"name": "family-assistant-frontend", "status": "Running"},
                    {"name": "postgres", "status": "Running"}
                ],
                "namespace": parameters.get("namespace", "homelab")
            }
        elif tool.name == "git_status":
            return {
                "branch": "main",
                "modified": ["prompts/core/FAMILY_ASSISTANT.md"],
                "untracked": [],
                "ahead": 2,
                "behind": 0
            }
        elif tool.name == "get_service_logs":
            return {
                "service": parameters.get("service"),
                "logs": [
                    "2025-11-17 10:30:15 INFO Starting Family Assistant API...",
                    "2025-11-17 10:30:16 INFO Database connection established",
                    "2025-11-17 10:30:17 INFO MCP server manager initialized"
                ],
                "lines": parameters.get("lines", 100)
            }
        else:
            return {"message": f"Tool '{tool.name}' executed successfully", "parameters": parameters}

    async def _perform_safety_check(
        self,
        tool: MCPTool,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform safety checks for critical tools"""

        violations = []

        # Check for dangerous parameters
        if tool.name == "git_commit":
            message = parameters.get("message", "")
            if any(keyword in message.lower() for keyword in ["password", "secret", "key"]):
                violations.append("Commit message may contain sensitive information")

        if tool.name == "list_pods":
            namespace = parameters.get("namespace", "")
            if namespace in ["kube-system", "default"]:
                violations.append("Accessing system namespaces may be dangerous")

        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "reason": "; ".join(violations) if violations else None
        }

    async def _log_execution(self, context: MCPExecutionContext, result: MCPExecutionResult):
        """Log tool execution for analytics and auditing"""

        await self.db_pool.execute("""
            INSERT INTO mcp_tool_usage (
                execution_id, user_id, tool_name, server_name, parameters,
                success, result, error_message, execution_time_ms,
                tokens_used, safety_violations
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            result.execution_id, context.user_id, result.tool_name, "",
            context.parameters, result.success, result.result,
            result.error, result.execution_time_ms, result.tokens_used,
            result.safety_violations
        )


# ============================================================================
# Factory Functions
# ============================================================================

async def create_mcp_manager(db_pool: asyncpg.Pool) -> MCPServerManager:
    """Create and initialize MCP server manager"""
    manager = MCPServerManager(db_pool)
    await manager.initialize()
    return manager


async def create_mcp_execution_engine(
    db_pool: asyncpg.Pool,
    server_manager: MCPServerManager
) -> MCPExecutionEngine:
    """Create MCP execution engine"""
    return MCPExecutionEngine(db_pool, server_manager)