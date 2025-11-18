"""
MCP Metrics and Monitoring Service

Provides comprehensive metrics collection, monitoring, and analytics
for MCP server usage, performance, and system health.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncpg

from api.services.mcp_manager import MCPServerManager, MCPExecutionEngine


@dataclass
class MCPMetricsSnapshot:
    """Snapshot of MCP metrics at a point in time"""
    timestamp: datetime
    total_servers: int
    online_servers: int
    total_tools: int
    active_executions: int
    avg_response_time_ms: float
    success_rate_1h: float
    error_rate_1h: float
    token_usage_24h: int
    top_tools_24h: List[Dict[str, Any]]
    role_usage_24h: Dict[str, int]


class MCPMetricsCollector:
    """Collects and aggregates MCP metrics"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self._cache_timeout = 60  # Cache metrics for 60 seconds
        self._cached_metrics: Optional[MCPMetricsSnapshot] = None
        self._cache_timestamp: Optional[datetime] = None

    async def get_current_metrics(
        self,
        force_refresh: bool = False
    ) -> MCPMetricsSnapshot:
        """Get current MCP metrics with caching"""

        now = datetime.utcnow()

        # Check cache
        if (not force_refresh and
            self._cached_metrics and
            self._cache_timestamp and
            (now - self._cache_timestamp).total_seconds() < self._cache_timeout):
            return self._cached_metrics

        # Collect fresh metrics
        metrics = await self._collect_metrics()

        # Update cache
        self._cached_metrics = metrics
        self._cache_timestamp = now

        return metrics

    async def _collect_metrics(self) -> MCPMetricsSnapshot:
        """Collect all MCP metrics from database and system"""

        # System metrics
        total_servers = await self.db_pool.fetchval(
            "SELECT COUNT(*) FROM mcp_servers"
        )

        online_servers = await self.db_pool.fetchval(
            "SELECT COUNT(*) FROM mcp_servers WHERE status = 'online'"
        )

        total_tools = await self.db_pool.fetchval(
            "SELECT COUNT(*) FROM mcp_servers, jsonb_array_elements(tools) as tool"
        )

        # Usage metrics (last 24 hours)
        now_24h = datetime.utcnow() - timedelta(hours=24)

        total_executions_24h = await self.db_pool.fetchval("""
            SELECT COUNT(*) FROM mcp_tool_usage
            WHERE timestamp >= $1
        """, now_24h)

        successful_executions_24h = await self.db_pool.fetchval("""
            SELECT COUNT(*) FROM mcp_tool_usage
            WHERE timestamp >= $1 AND success = true
        """, now_24h)

        success_rate_24h = (
            (successful_executions_24h / total_executions_24h * 100)
            if total_executions_24h > 0 else 0
        )

        # Performance metrics (last hour)
        now_1h = datetime.utcnow() - timedelta(hours=1)

        avg_response_time = await self.db_pool.fetchval("""
            SELECT AVG(execution_time_ms) FROM mcp_tool_usage
            WHERE timestamp >= $1 AND success = true
        """, now_1h) or 0

        error_rate_1h = await self.db_pool.fetchval("""
            SELECT 100.0 - (AVG(CASE WHEN success = true THEN 100 ELSE 0 END))
            FROM mcp_tool_usage
            WHERE timestamp >= $1
        """, now_1h) or 0

        # Token usage (24h)
        token_usage_24h = await self.db_pool.fetchval("""
            SELECT COALESCE(SUM(tokens_used), 0) FROM mcp_tool_usage
            WHERE timestamp >= $1 AND tokens_used IS NOT NULL
        """, now_24h) or 0

        # Top tools (24h)
        top_tools = await self.db_pool.fetch("""
            SELECT
                tool_name,
                COUNT(*) as usage_count,
                AVG(execution_time_ms) as avg_time_ms,
                COUNT(CASE WHEN success = true THEN 1 END) as success_count
            FROM mcp_tool_usage
            WHERE timestamp >= $1
            GROUP BY tool_name
            ORDER BY usage_count DESC
            LIMIT 10
        """, now_24h)

        top_tools_data = [
            {
                "tool_name": row["tool_name"],
                "usage_count": row["usage_count"],
                "avg_time_ms": round(row["avg_time_ms"] or 0, 2),
                "success_rate": round(
                    (row["success_count"] / row["usage_count"] * 100)
                    if row["usage_count"] > 0 else 0, 2
                )
            }
            for row in top_tools
        ]

        # Role usage (24h)
        role_usage = await self.db_pool.fetch("""
            SELECT
                fm.role,
                COUNT(*) as usage_count
            FROM mcp_tool_usage mu
            JOIN family_members fm ON mu.user_id = fm.id
            WHERE mu.timestamp >= $1
            GROUP BY fm.role
            ORDER BY usage_count DESC
        """, now_24h)

        role_usage_data = {
            row["role"]: row["usage_count"] for row in role_usage
        }

        # Active executions (currently running)
        active_executions = await self.db_pool.fetchval("""
            SELECT COUNT(*) FROM mcp_tool_usage
            WHERE success IS NULL AND timestamp >= NOW() - INTERVAL '5 minutes'
        """)

        return MCPMetricsSnapshot(
            timestamp=datetime.utcnow(),
            total_servers=total_servers,
            online_servers=online_servers,
            total_tools=total_tools,
            active_executions=active_executions,
            avg_response_time_ms=round(avg_response_time, 2),
            success_rate_1h=round(success_rate_24h, 2),
            error_rate_1h=round(error_rate_1h, 2),
            token_usage_24h=token_usage_24h,
            top_tools_24h=top_tools_data,
            role_usage_24h=role_usage_data
        )

    async def get_usage_trends(
        self,
        days: int = 7,
        granularity: str = "hour"
    ) -> List[Dict[str, Any]]:
        """Get usage trends over time"""

        if granularity == "hour":
            interval = "1 hour"
        elif granularity == "day":
            interval = "1 day"
        else:
            interval = "1 hour"

        start_date = datetime.utcnow() - timedelta(days=days)

        rows = await self.db_pool.fetch(f"""
            SELECT
                date_trunc('{granularity}', timestamp) as time_bucket,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_executions,
                AVG(execution_time_ms) as avg_response_time_ms,
                COALESCE(SUM(tokens_used), 0) as total_tokens
            FROM mcp_tool_usage
            WHERE timestamp >= $1
            GROUP BY time_bucket
            ORDER BY time_bucket DESC
        """, start_date)

        trends = []
        for row in rows:
            success_rate = (
                (row["successful_executions"] / row["total_executions"] * 100)
                if row["total_executions"] > 0 else 0
            )

            trends.append({
                "timestamp": row["time_bucket"].isoformat(),
                "total_executions": row["total_executions"],
                "successful_executions": row["successful_executions"],
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(row["avg_response_time_ms"] or 0, 2),
                "total_tokens": row["total_tokens"]
            })

        return trends

    async def get_tool_performance_report(
        self,
        tool_name: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get detailed performance report for tools"""

        start_date = datetime.utcnow() - timedelta(days=days)

        # Filter by tool if specified
        tool_filter = "AND mu.tool_name = $2" if tool_name else ""
        params = [start_date] + ([tool_name] if tool_name else [])

        rows = await self.db_pool.fetch(f"""
            SELECT
                mu.tool_name,
                mu.server_name,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN mu.success = true THEN 1 END) as successful_executions,
                AVG(mu.execution_time_ms) as avg_response_time_ms,
                MIN(mu.execution_time_ms) as min_response_time_ms,
                MAX(mu.execution_time_ms) as max_response_time_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY mu.execution_time_ms) as p95_response_time_ms,
                COALESCE(SUM(mu.tokens_used), 0) as total_tokens,
                COUNT(CASE WHEN mu.safety_violations IS NOT NULL AND jsonb_array_length(mu.safety_violations) > 0 THEN 1 END) as safety_violations
            FROM mcp_tool_usage mu
            WHERE mu.timestamp >= $1 {tool_filter}
            GROUP BY mu.tool_name, mu.server_name
            ORDER BY total_executions DESC
        """, *params)

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "tools": []
        }

        for row in rows:
            success_rate = (
                (row["successful_executions"] / row["total_executions"] * 100)
                if row["total_executions"] > 0 else 0
            )

            tool_report = {
                "tool_name": row["tool_name"],
                "server_name": row["server_name"],
                "total_executions": row["total_executions"],
                "successful_executions": row["successful_executions"],
                "success_rate": round(success_rate, 2),
                "response_time": {
                    "avg_ms": round(row["avg_response_time_ms"] or 0, 2),
                    "min_ms": row["min_response_time_ms"] or 0,
                    "max_ms": row["max_response_time_ms"] or 0,
                    "p95_ms": round(row["p95_response_time_ms"] or 0, 2)
                },
                "total_tokens": row["total_tokens"],
                "safety_violations": row["safety_violations"],
                "performance_grade": self._calculate_performance_grade(
                    success_rate, row["avg_response_time_ms"] or 0
                )
            }

            report["tools"].append(tool_report)

        return report

    def _calculate_performance_grade(
        self,
        success_rate: float,
        avg_response_time: float
    ) -> str:
        """Calculate performance grade based on success rate and response time"""

        if success_rate >= 95 and avg_response_time < 1000:
            return "A"
        elif success_rate >= 90 and avg_response_time < 2000:
            return "B"
        elif success_rate >= 80 and avg_response_time < 5000:
            return "C"
        elif success_rate >= 70:
            return "D"
        else:
            return "F"

    async def get_user_activity_report(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get user activity and engagement report"""

        start_date = datetime.utcnow() - timedelta(days=days)

        rows = await self.db_pool.fetch("""
            SELECT
                fm.id,
                fm.first_name,
                fm.last_name,
                fm.role,
                COUNT(DISTINCT DATE(mu.timestamp)) as active_days,
                COUNT(*) as total_executions,
                COUNT(CASE WHEN mu.success = true THEN 1 END) as successful_executions,
                AVG(mu.execution_time_ms) as avg_response_time_ms,
                COUNT(DISTINCT mu.tool_name) as unique_tools_used,
                COALESCE(SUM(mu.tokens_used), 0) as total_tokens
            FROM mcp_tool_usage mu
            JOIN family_members fm ON mu.user_id = fm.id
            WHERE mu.timestamp >= $1
            GROUP BY fm.id, fm.first_name, fm.last_name, fm.role
            ORDER BY total_executions DESC
        """, start_date)

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "users": []
        }

        for row in rows:
            success_rate = (
                (row["successful_executions"] / row["total_executions"] * 100)
                if row["total_executions"] > 0 else 0
            )

            user_report = {
                "user_id": str(row["id"]),
                "name": f"{row['first_name']} {row['last_name']}",
                "role": row["role"],
                "active_days": row["active_days"],
                "total_executions": row["total_executions"],
                "successful_executions": row["successful_executions"],
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(row["avg_response_time_ms"] or 0, 2),
                "unique_tools_used": row["unique_tools_used"],
                "total_tokens": row["total_tokens"],
                "engagement_score": self._calculate_engagement_score(
                    row["active_days"], days, row["total_executions"]
                )
            }

            report["users"].append(user_report)

        return report

    def _calculate_engagement_score(
        self,
        active_days: int,
        total_days: int,
        total_executions: int
    ) -> str:
        """Calculate user engagement score"""

        activity_ratio = active_days / total_days if total_days > 0 else 0
        execution_frequency = total_executions / active_days if active_days > 0 else 0

        if activity_ratio >= 0.8 and execution_frequency >= 5:
            return "High"
        elif activity_ratio >= 0.5 and execution_frequency >= 2:
            return "Medium"
        elif activity_ratio >= 0.2:
            return "Low"
        else:
            return "Minimal"

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts based on MCP metrics"""

        alerts = []
        now = datetime.utcnow()

        # Check for offline servers
        offline_servers = await self.db_pool.fetch("""
            SELECT name, last_health_check, error_message
            FROM mcp_servers
            WHERE status != 'online' AND last_health_check < NOW() - INTERVAL '10 minutes'
        """)

        for server in offline_servers:
            alerts.append({
                "id": f"server_offline_{server['name']}",
                "type": "error",
                "title": f"MCP Server Offline: {server['name']}",
                "message": f"Server '{server['name']}' has been offline since {server['last_health_check']}",
                "details": {
                    "server_name": server["name"],
                    "error_message": server["error_message"],
                    "last_check": server["last_health_check"].isoformat()
                },
                "timestamp": now.isoformat()
            })

        # Check for high error rates
        error_rate_1h = await self.db_pool.fetchval("""
            SELECT 100.0 - (AVG(CASE WHEN success = true THEN 100 ELSE 0 END))
            FROM mcp_tool_usage
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
        """)

        if error_rate_1h and error_rate_1h > 20:
            alerts.append({
                "id": "high_error_rate",
                "type": "warning",
                "title": "High MCP Error Rate",
                "message": f"MCP tool error rate is {error_rate_1h:.1f}% in the last hour",
                "details": {
                    "error_rate": round(error_rate_1h, 2),
                    "threshold": 20
                },
                "timestamp": now.isoformat()
            })

        # Check for slow response times
        avg_response_time = await self.db_pool.fetchval("""
            SELECT AVG(execution_time_ms)
            FROM mcp_tool_usage
            WHERE timestamp >= NOW() - INTERVAL '1 hour' AND success = true
        """)

        if avg_response_time and avg_response_time > 5000:
            alerts.append({
                "id": "slow_response_time",
                "type": "warning",
                "title": "Slow MCP Response Times",
                "message": f"Average MCP response time is {avg_response_time:.0f}ms",
                "details": {
                    "avg_response_time_ms": round(avg_response_time, 0),
                    "threshold_ms": 5000
                },
                "timestamp": now.isoformat()
            })

        # Check for recent safety violations
        safety_violations = await self.db_pool.fetchval("""
            SELECT COUNT(*)
            FROM mcp_tool_usage
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            AND safety_violations IS NOT NULL
            AND jsonb_array_length(safety_violations) > 0
        """)

        if safety_violations > 0:
            alerts.append({
                "id": "safety_violations",
                "type": "warning",
                "title": "MCP Safety Violations Detected",
                "message": f"{safety_violations} safety violations in the last 24 hours",
                "details": {
                    "violation_count": safety_violations,
                    "period_hours": 24
                },
                "timestamp": now.isoformat()
            })

        return alerts

    async def cleanup_old_metrics(self, days_to_keep: int = 90):
        """Clean up old usage metrics data"""

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        deleted_rows = await self.db_pool.fetchval("""
            DELETE FROM mcp_tool_usage
            WHERE timestamp < $1
            RETURNING COUNT(*)
        """, cutoff_date)

        return deleted_rows or 0


# ============================================================================
# Factory Functions
# ============================================================================

async def create_mcp_metrics_collector(db_pool: asyncpg.Pool) -> MCPMetricsCollector:
    """Create MCP metrics collector instance"""
    return MCPMetricsCollector(db_pool)