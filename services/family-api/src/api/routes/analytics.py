"""
Sub-Agent Analytics API Routes

Endpoints for querying sub-agent execution traces, performance metrics,
and historical analytics data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncpg

from api.dependencies import get_current_admin_user
from api.models.user_management import FamilyMember


# Pydantic models for API responses
class ExecutionOverview(BaseModel):
    """Overview statistics for sub-agent executions."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_response_time_ms: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    agent_breakdown: Dict[str, int]
    time_range_hours: int = 24


class ToolCallDetail(BaseModel):
    """Detailed information about a tool call."""
    tool_name: str
    agent_id: str
    call_index: int
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    duration_ms: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime


class ExecutionTrace(BaseModel):
    """Detailed execution trace for a single sub-agent request."""
    execution_id: str
    user_id: Optional[str]
    conversation_id: Optional[str]
    request_text: str
    timestamp: datetime

    # Intent classification
    agent_id: str
    confidence: float
    keywords: List[str]
    intent_duration_ms: int

    # Agent execution
    skill_prompt_size: int
    skill_prompt_tokens: int
    agent_duration_ms: int

    # Token breakdown
    total_tokens: Optional[int]
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]

    # Performance
    total_duration_ms: int
    success: bool
    error_message: Optional[str] = None

    # Tool calls
    tool_calls: List[ToolCallDetail] = []

    # Metadata
    metadata: Dict[str, Any] = {}


class OverviewResponse(BaseModel):
    """Response model for overview endpoint."""
    overview: ExecutionOverview
    recent_executions: List[Dict[str, Any]]


class TraceResponse(BaseModel):
    """Response model for trace detail endpoint."""
    trace: ExecutionTrace


# Create router
router = APIRouter(
    prefix="/api/v1/analytics/sub-agents",
    tags=["Analytics"]
)


async def get_db_pool():
    """Get database pool from app state (injected by startup)."""
    # This will be injected via dependency in main.py
    # For now, we'll access it from app state
    from api.main import db_pool
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_pool


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    hours: int = Query(24, ge=1, le=168, description="Time range in hours (1-168)"),
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    current_user: FamilyMember = Depends(get_current_admin_user)
):
    """
    Get overview dashboard summary for sub-agent executions.

    Returns:
        - Total executions count
        - Success rate
        - Average response time
        - Total tokens consumed
        - Agent breakdown (execution count per agent)
        - Recent executions (last 10)
    """
    try:
        db_pool = await get_db_pool()

        async with db_pool.acquire() as conn:
            # Build query with optional agent filter
            time_filter = f"timestamp > NOW() - INTERVAL '{hours} hours'"
            agent_filter = f"AND agent_id = '{agent_id}'" if agent_id else ""

            # Get aggregate statistics
            stats = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as total_executions,
                    COUNT(*) FILTER (WHERE success = true) as successful_executions,
                    COUNT(*) FILTER (WHERE success = false) as failed_executions,
                    AVG(total_duration_ms) as avg_response_time_ms,
                    SUM(COALESCE(total_tokens, 0)) as total_tokens,
                    SUM(COALESCE(prompt_tokens, 0)) as total_prompt_tokens,
                    SUM(COALESCE(completion_tokens, 0)) as total_completion_tokens
                FROM sub_agent_executions
                WHERE {time_filter} {agent_filter}
            """)

            # Get agent breakdown
            agent_breakdown_rows = await conn.fetch(f"""
                SELECT agent_id, COUNT(*) as count
                FROM sub_agent_executions
                WHERE {time_filter} {agent_filter}
                GROUP BY agent_id
                ORDER BY count DESC
            """)

            agent_breakdown = {row['agent_id']: row['count'] for row in agent_breakdown_rows}

            # Calculate success rate
            total = stats['total_executions'] or 0
            successful = stats['successful_executions'] or 0
            success_rate = (successful / total * 100) if total > 0 else 0.0

            # Get recent executions
            recent = await conn.fetch(f"""
                SELECT
                    execution_id, agent_id, request_text, timestamp,
                    total_duration_ms, success, confidence
                FROM sub_agent_executions
                WHERE {time_filter} {agent_filter}
                ORDER BY timestamp DESC
                LIMIT 10
            """)

            recent_executions = [
                {
                    "execution_id": str(row['execution_id']),
                    "agent_id": row['agent_id'],
                    "request_text": row['request_text'][:100] + "..." if len(row['request_text']) > 100 else row['request_text'],
                    "timestamp": row['timestamp'].isoformat(),
                    "duration_ms": row['total_duration_ms'],
                    "success": row['success'],
                    "confidence": row['confidence']
                }
                for row in recent
            ]

            overview = ExecutionOverview(
                total_executions=total,
                successful_executions=successful,
                failed_executions=stats['failed_executions'] or 0,
                success_rate=round(success_rate, 2),
                avg_response_time_ms=int(stats['avg_response_time_ms'] or 0),
                total_tokens=int(stats['total_tokens'] or 0),
                total_prompt_tokens=int(stats['total_prompt_tokens'] or 0),
                total_completion_tokens=int(stats['total_completion_tokens'] or 0),
                agent_breakdown=agent_breakdown,
                time_range_hours=hours
            )

            return OverviewResponse(
                overview=overview,
                recent_executions=recent_executions
            )

    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch overview: {str(e)}"
        )


@router.get("/traces/{execution_id}", response_model=TraceResponse)
async def get_execution_trace(
    execution_id: str,
    current_user: FamilyMember = Depends(get_current_admin_user)
):
    """
    Get detailed execution trace for a specific execution.

    Returns complete trace including:
        - Intent classification data
        - Agent execution metadata
        - Token breakdown
        - All tool calls with parameters and results
        - Performance timing at each stage
    """
    try:
        db_pool = await get_db_pool()

        async with db_pool.acquire() as conn:
            # Get execution details
            execution = await conn.fetchrow("""
                SELECT
                    execution_id, user_id, conversation_id, request_text, timestamp,
                    agent_id, confidence, keywords, intent_duration_ms,
                    skill_prompt_size, skill_prompt_tokens, agent_duration_ms,
                    total_tokens, prompt_tokens, completion_tokens,
                    total_duration_ms, success, error_message, metadata
                FROM sub_agent_executions
                WHERE execution_id = $1
            """, execution_id)

            if not execution:
                raise HTTPException(
                    status_code=404,
                    detail=f"Execution {execution_id} not found"
                )

            # Get tool calls
            tool_calls_rows = await conn.fetch("""
                SELECT
                    tool_name, agent_id, call_index,
                    parameters, result, duration_ms,
                    success, error_message, timestamp
                FROM sub_agent_tool_calls
                WHERE execution_id = $1
                ORDER BY call_index ASC
            """, execution_id)

            tool_calls = [
                ToolCallDetail(
                    tool_name=row['tool_name'],
                    agent_id=row['agent_id'],
                    call_index=row['call_index'],
                    parameters=row['parameters'] or {},
                    result=row['result'] or {},
                    duration_ms=row['duration_ms'] or 0,
                    success=row['success'],
                    error_message=row['error_message'],
                    timestamp=row['timestamp']
                )
                for row in tool_calls_rows
            ]

            trace = ExecutionTrace(
                execution_id=str(execution['execution_id']),
                user_id=str(execution['user_id']) if execution['user_id'] else None,
                conversation_id=execution['conversation_id'],
                request_text=execution['request_text'],
                timestamp=execution['timestamp'],
                agent_id=execution['agent_id'],
                confidence=execution['confidence'],
                keywords=execution['keywords'] or [],
                intent_duration_ms=execution['intent_duration_ms'] or 0,
                skill_prompt_size=execution['skill_prompt_size'] or 0,
                skill_prompt_tokens=execution['skill_prompt_tokens'] or 0,
                agent_duration_ms=execution['agent_duration_ms'] or 0,
                total_tokens=execution['total_tokens'],
                prompt_tokens=execution['prompt_tokens'],
                completion_tokens=execution['completion_tokens'],
                total_duration_ms=execution['total_duration_ms'],
                success=execution['success'],
                error_message=execution['error_message'],
                tool_calls=tool_calls,
                metadata=execution['metadata'] or {}
            )

            return TraceResponse(trace=trace)

    except HTTPException:
        raise
    except asyncpg.PostgresError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trace: {str(e)}"
        )
