"""
Family Tools Manager - Simplified Member Interface

Provides family members with easy access to pre-configured tools
without server management complexity.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

import asyncpg
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FamilyTool(BaseModel):
    """Represents a tool available to family members"""
    name: str
    description: str
    category: str
    server_name: str
    icon: Optional[str] = None
    personal_data_risk: str
    requires_parent_approval: bool
    usage_count: int
    is_enabled: bool
    last_used: Optional[datetime] = None


class FamilyToolExecution(BaseModel):
    """Tool execution request from family member"""
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class FamilyToolsManager:
    """Manages tool access for family members"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def initialize(self):
        """Initialize family tools system"""
        await self._create_family_tools_tables()
        logger.info("Family Tools Manager initialized")

    async def _create_family_tools_tables(self):
        """Create family tools usage tables"""

        # Family tool execution logs
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS family_tool_executions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                execution_id VARCHAR(100) UNIQUE NOT NULL,
                user_id UUID NOT NULL REFERENCES family_members(id),
                tool_name VARCHAR(200) NOT NULL,
                parameters JSONB DEFAULT '{}',
                context JSONB,
                success BOOLEAN NOT NULL,
                result JSONB,
                error_message TEXT,
                execution_time_ms INTEGER,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                personal_data_accessed BOOLEAN DEFAULT false
            )
        """)

        # Family member tool favorites
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS family_member_tool_favorites (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                tool_name VARCHAR(200) NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW(),

                UNIQUE(user_id, tool_name)
            )
        """)

        # Tool recommendations cache
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS family_tool_recommendations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                tool_name VARCHAR(200) NOT NULL,
                recommendation_reason VARCHAR(200),
                score DECIMAL(3,2),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ,

                UNIQUE(user_id, tool_name)
            )
        """)

        # Indexes
        await self.db_pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_family_tool_executions_user_timestamp
            ON family_tool_executions(user_id, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_family_tool_executions_tool_timestamp
            ON family_tool_executions(tool_name, timestamp DESC);

            CREATE INDEX IF NOT EXISTS idx_family_tool_recommendations_score
            ON family_tool_recommendations(user_id, score DESC);
        """)

    async def get_available_tools(
        self,
        user_id: str,
        user_role: str
    ) -> List[FamilyTool]:
        """Get tools available to a specific family member"""
        try:
            rows = await self.db_pool.fetch("""
                SELECT
                    sta.tool_name,
                    sta.personal_data_risk,
                    sta.requires_parent_approval,
                    ams.name as server_name,
                    ams.connection_type,
                    COALESCE(ftmp.usage_count, 0) as usage_count,
                    COALESCE(ftmp.is_enabled, true) as is_enabled,
                    ftmp.last_used
                FROM system_tool_availability sta
                JOIN admin_mcp_servers ams ON sta.server_id = ams.id
                LEFT JOIN family_member_tool_preferences ftmp ON
                    sta.tool_name = ftmp.tool_name AND ftmp.user_id = $1
                WHERE
                    sta.is_enabled = true AND
                    ams.is_enabled = true AND
                    $2 = ANY(sta.family_roles)
                ORDER BY
                    CASE WHEN ftmp.usage_count > 0 THEN 1 ELSE 2 END,
                    ftmp.usage_count DESC,
                    sta.tool_name
            """, user_id, user_role)

            tools = []
            for row in rows:
                # Generate description and category based on tool name
                description, category, icon = self._generate_tool_metadata(row["tool_name"])

                tool = FamilyTool(
                    name=row["tool_name"],
                    description=description,
                    category=category,
                    server_name=row["server_name"],
                    icon=icon,
                    personal_data_risk=row["personal_data_risk"],
                    requires_parent_approval=row["requires_parent_approval"],
                    usage_count=row["usage_count"],
                    is_enabled=row["is_enabled"],
                    last_used=row["last_used"]
                )
                tools.append(tool)

            return tools
        except Exception as e:
            logger.error(f"Failed to get available tools for user {user_id}: {e}")
            return []

    def _generate_tool_metadata(self, tool_name: str) -> tuple[str, str, str]:
        """Generate description, category, and icon for tool"""
        name_lower = tool_name.lower()

        # Category mappings
        if any(keyword in name_lower for keyword in ["calendar", "schedule", "appointment", "event"]):
            return f"Manage {tool_name} and schedule events", "calendar", "📅"
        elif any(keyword in name_lower for keyword in ["note", "todo", "task", "reminder"]):
            return f"Create and manage {tool_name}", "notes", "📝"
        elif any(keyword in name_lower for keyword in ["weather", "forecast", "temperature"]):
            return f"Check {tool_name} and weather conditions", "weather", "🌤️"
        elif any(keyword in name_lower for keyword in ["news", "article", "story"]):
            return f"Read {tool_name} and stay informed", "news", "📰")
        elif any(keyword in name_lower for keyword in ["translate", "language", "dictionary"]):
            return f"Use {tool_name} for translation help", "education", "🌐"
        elif any(keyword in name_lower for keyword in ["calculate", "math", "converter"]):
            return f"Use {tool_name} for calculations", "productivity", "🧮")
        elif any(keyword in name_lower for keyword in ["search", "find", "lookup"]):
            return f"Use {tool_name} to search information", "general", "🔍")
        else:
            return f"Use {tool_name} for various tasks", "general", "🔧"

    async def execute_tool(
        self,
        user_id: str,
        execution: FamilyToolExecution
    ) -> Dict[str, Any]:
        """Execute a tool for a family member"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            # Check if tool is available and enabled for user
            user_role = await self.db_pool.fetchval(
                "SELECT role FROM family_members WHERE id = $1",
                user_id
            )

            if not user_role:
                return {
                    "success": False,
                    "error": "User not found",
                    "execution_id": execution_id
                }

            # Check tool availability
            tool_available = await self.db_pool.fetchrow("""
                SELECT
                    sta.personal_data_risk,
                    sta.requires_parent_approval,
                    sta.family_roles
                FROM system_tool_availability sta
                WHERE
                    sta.tool_name = $1 AND
                    sta.is_enabled = true AND
                    $2 = ANY(sta.family_roles)
            """, execution.tool_name, user_role)

            if not tool_available:
                return {
                    "success": False,
                    "error": "Tool not available or not permitted",
                    "execution_id": execution_id
                }

            # Check parental approval if required
            if tool_available["requires_parent_approval"]:
                approval_needed = await self._check_parental_approval(
                    user_id, execution.tool_name, execution.parameters
                )
                if not approval_needed:
                    return {
                        "success": False,
                        "error": "Parental approval required for this tool",
                        "execution_id": execution_id
                    }

            # Execute tool (mock implementation for now)
            result = await self._execute_tool_logic(execution, tool_available)

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Update usage statistics
            await self._update_tool_usage(user_id, execution.tool_name, execution_time, True)

            # Log execution
            await self._log_execution(
                execution_id, user_id, execution, True, result, None, execution_time
            )

            return {
                "execution_id": execution_id,
                "success": True,
                "result": result,
                "execution_time_ms": execution_time
            }

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Log error
            await self._log_execution(
                execution_id, user_id, execution, False, None, str(e), execution_time
            )

            return {
                "execution_id": execution_id,
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }

    async def _check_parental_approval(
        self,
        user_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """Check if parental approval is required and granted"""
        # For now, always approve (this can be extended with actual approval workflow)
        # In a real implementation, you might:
        # - Check for pre-approved tools
        # - Send notification to parents
        # - Check approval history
        # - Implement time-based approvals
        return True

    async def _execute_tool_logic(
        self,
        execution: FamilyToolExecution,
        tool_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual tool logic (mock implementation)"""
        tool_name = execution.tool_name.lower()

        # Mock different tool behaviors based on name
        if "calendar" in tool_name:
            return {
                "message": f"Checked your calendar for today",
                "events": [
                    {"time": "10:00 AM", "title": "Math homework due"},
                    {"time": "2:00 PM", "title": "Soccer practice"},
                    {"time": "7:00 PM", "title": "Family dinner"}
                ],
                "source": "family_calendar"
            }
        elif "weather" in tool_name:
            return {
                "message": "Today's weather forecast",
                "temperature": "72°F",
                "conditions": "Partly cloudy",
                "humidity": "65%",
                "source": "weather_service"
            }
        elif "note" in tool_name or "todo" in tool_name:
            return {
                "message": f"Added to your notes: {execution.parameters.get('text', 'New note')}",
                "note_id": f"note_{uuid.uuid4().hex[:8]}",
                "source": "family_notes"
            }
        elif "translate" in tool_name:
            text = execution.parameters.get("text", "")
            return {
                "message": f"Translation complete",
                "original": text,
                "translated": f"[Translated version of: {text}]",
                "source": "translation_service"
            }
        else:
            return {
                "message": f"Tool '{execution.tool_name}' executed successfully",
                "parameters": execution.parameters,
                "source": "family_tools"
            }

    async def _update_tool_usage(
        self,
        user_id: str,
        tool_name: str,
        execution_time_ms: int,
        success: bool
    ):
        """Update tool usage statistics"""
        try:
            # Update or create user tool preference
            await self.db_pool.execute("""
                INSERT INTO family_member_tool_preferences (
                    user_id, tool_name, usage_count, last_used
                ) VALUES ($1, $2, 1, NOW())
                ON CONFLICT (user_id, tool_name)
                DO UPDATE SET
                    usage_count = family_member_tool_preferences.usage_count + 1,
                    last_used = NOW(),
                    updated_at = NOW()
            """, user_id, tool_name)

        except Exception as e:
            logger.error(f"Failed to update tool usage: {e}")

    async def _log_execution(
        self,
        execution_id: str,
        user_id: str,
        execution: FamilyToolExecution,
        success: bool,
        result: Optional[Any],
        error: Optional[str],
        execution_time_ms: int
    ):
        """Log tool execution"""
        try:
            await self.db_pool.execute("""
                INSERT INTO family_tool_executions (
                    execution_id, user_id, tool_name, parameters, context,
                    success, result, error_message, execution_time_ms
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, execution_id, user_id, execution.tool_name,
                  execution.parameters, execution.context, success,
                  result, error, execution_time_ms)
        except Exception as e:
            logger.error(f"Failed to log execution: {e}")

    async def add_favorite(self, user_id: str, tool_name: str) -> bool:
        """Add tool to user favorites"""
        try:
            await self.db_pool.execute("""
                INSERT INTO family_member_tool_favorites (user_id, tool_name)
                VALUES ($1, $2)
                ON CONFLICT (user_id, tool_name) DO NOTHING
            """, user_id, tool_name)
            return True
        except Exception as e:
            logger.error(f"Failed to add favorite: {e}")
            return False

    async def remove_favorite(self, user_id: str, tool_name: str) -> bool:
        """Remove tool from user favorites"""
        try:
            result = await self.db_pool.execute("""
                DELETE FROM family_member_tool_favorites
                WHERE user_id = $1 AND tool_name = $2
            """, user_id, tool_name)
            return result == "DELETE 1"
        except Exception as e:
            logger.error(f"Failed to remove favorite: {e}")
            return False

    async def get_favorites(self, user_id: str, user_role: str) -> List[FamilyTool]:
        """Get user's favorite tools"""
        try:
            rows = await self.db_pool.fetch("""
                SELECT
                    sta.tool_name,
                    sta.personal_data_risk,
                    sta.requires_parent_approval,
                    ams.name as server_name,
                    COALESCE(ftmp.usage_count, 0) as usage_count,
                    ftmp.last_used
                FROM family_member_tool_favorites fmtf
                JOIN system_tool_availability sta ON fmtf.tool_name = sta.tool_name
                JOIN admin_mcp_servers ams ON sta.server_id = ams.id
                LEFT JOIN family_member_tool_preferences ftmp ON
                    sta.tool_name = ftmp.tool_name AND ftmp.user_id = $1
                WHERE
                    fmtf.user_id = $1 AND
                    sta.is_enabled = true AND
                    ams.is_enabled = true AND
                    $2 = ANY(sta.family_roles)
                ORDER BY fmtf.added_at DESC
            """, user_id, user_role)

            favorites = []
            for row in rows:
                description, category, icon = self._generate_tool_metadata(row["tool_name"])

                favorite = FamilyTool(
                    name=row["tool_name"],
                    description=description,
                    category=category,
                    server_name=row["server_name"],
                    icon=icon,
                    personal_data_risk=row["personal_data_risk"],
                    requires_parent_approval=row["requires_parent_approval"],
                    usage_count=row["usage_count"],
                    is_enabled=True,
                    last_used=row["last_used"]
                )
                favorites.append(favorite)

            return favorites
        except Exception as e:
            logger.error(f"Failed to get favorites: {e}")
            return []

    async def get_recommendations(
        self,
        user_id: str,
        user_role: str
    ) -> List[Dict[str, Any]]:
        """Get tool recommendations for user"""
        try:
            # Get user's recent usage patterns
            recent_tools = await self.db_pool.fetch("""
                SELECT tool_name, COUNT(*) as usage_count
                FROM family_tool_executions
                WHERE user_id = $1 AND success = true AND timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY tool_name
                ORDER BY usage_count DESC
                LIMIT 5
            """, user_id)

            # Get available tools the user hasn't tried
            all_tools = await self.get_available_tools(user_id, user_role)
            used_tools = {row["tool_name"] for row in recent_tools}

            recommendations = []
            for tool in all_tools:
                if tool.name not in used_tools and tool.personal_data_risk != "high":
                    recommendations.append({
                        "name": tool.name,
                        "description": tool.description,
                        "category": tool.category,
                        "icon": tool.icon,
                        "reason": "New tool you might like",
                        "score": 0.8
                    })

            return recommendations[:5]  # Return top 5 recommendations

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []

    async def get_usage_history(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get user's tool usage history"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            rows = await self.db_pool.fetch("""
                SELECT
                    execution_id,
                    tool_name,
                    success,
                    execution_time_ms,
                    timestamp,
                    error_message
                FROM family_tool_executions
                WHERE user_id = $1 AND timestamp >= $2
                ORDER BY timestamp DESC
                LIMIT 50
            """, user_id, start_date)

            history = []
            for row in rows:
                history.append({
                    "execution_id": row["execution_id"],
                    "tool_name": row["tool_name"],
                    "success": row["success"],
                    "execution_time_ms": row["execution_time_ms"],
                    "timestamp": row["timestamp"].isoformat(),
                    "error_message": row["error_message"]
                })

            return history
        except Exception as e:
            logger.error(f"Failed to get usage history: {e}")
            return []


# ============================================================================
# Factory Functions
# ============================================================================

async def create_family_tools_manager(db_pool: asyncpg.Pool) -> FamilyToolsManager:
    """Create family tools manager instance"""
    manager = FamilyToolsManager(db_pool)
    await manager.initialize()
    return manager