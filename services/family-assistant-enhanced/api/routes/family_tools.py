"""
Family Tools API Routes

Simplified interface for family members to access and use
pre-configured tools without complex setup.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from api.dependencies import get_current_user_from_token, get_db_pool
from api.models.user_management import FamilyMember
from api.services.family_tools_manager import FamilyToolsManager, FamilyTool, FamilyToolExecution
import asyncpg


router = APIRouter(prefix="/api/v1/family-tools", tags=["Family Tools"])


# ============================================================================
# Pydantic Models for API
# ============================================================================

class ToolExecutionRequest(BaseModel):
    """Model for tool execution request"""
    tool_name: str = Field(..., description="Tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class FavoriteToolRequest(BaseModel):
    """Model for favorite tool management"""
    tool_name: str = Field(..., description="Tool name")


# ============================================================================
# Dependencies
# ============================================================================

async def get_family_tools_manager(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> FamilyToolsManager:
    """Get family tools manager instance"""
    from api.services.family_tools_manager import create_family_tools_manager
    return await create_family_tools_manager(db_pool)


# ============================================================================
# Tool Discovery and Browsing
# ============================================================================

@router.get("/tools", response_model=List[Dict[str, Any]])
async def browse_available_tools(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search tools")
):
    """Browse tools available to the current user"""
    try:
        tools = await tools_manager.get_available_tools(
            str(current_user.id),
            current_user.role.value
        )

        # Apply filters
        if category:
            tools = [t for t in tools if t.category == category]

        if search:
            search_lower = search.lower()
            tools = [
                t for t in tools
                if search_lower in t.name.lower() or
                   search_lower in t.description.lower() or
                   search_lower in t.server_name.lower()
            ]

        # Convert to dict format
        tool_list = []
        for tool in tools:
            tool_list.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "server_name": tool.server_name,
                "icon": tool.icon,
                "personal_data_risk": tool.personal_data_risk,
                "requires_parent_approval": tool.requires_parent_approval,
                "usage_count": tool.usage_count,
                "is_enabled": tool.is_enabled,
                "last_used": tool.last_used.isoformat() if tool.last_used else None
            })

        return tool_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to browse tools: {str(e)}"
        )


@router.get("/tools/categories")
async def get_tool_categories(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Get available tool categories"""
    try:
        tools = await tools_manager.get_available_tools(
            str(current_user.id),
            current_user.role.value
        )

        # Count tools by category
        categories = {}
        for tool in tools:
            if tool.category not in categories:
                categories[tool.category] = {
                    "name": tool.category,
                    "icon": tool.icon,
                    "tool_count": 0,
                    "description": _get_category_description(tool.category)
                }
            categories[tool.category]["tool_count"] += 1

        return list(categories.values())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


def _get_category_description(category: str) -> str:
    """Get description for a tool category"""
    descriptions = {
        "calendar": "Manage your schedule and events",
        "notes": "Create and manage notes and tasks",
        "weather": "Check weather forecasts and conditions",
        "news": "Read news and stay informed",
        "education": "Learning and educational tools",
        "productivity": "Productivity and task management",
        "communication": "Messaging and communication tools",
        "general": "General purpose tools and utilities",
        "entertainment": "Games and entertainment"
    }
    return descriptions.get(category, "Tools for various tasks")


# ============================================================================
# Tool Execution
# ============================================================================

@router.post("/tools/execute")
async def execute_tool(
    execution: ToolExecutionRequest,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Execute a tool"""
    try:
        # Validate tool parameters
        if not execution.tool_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tool name is required"
            )

        # Create execution request
        tool_execution = FamilyToolExecution(
            tool_name=execution.tool_name,
            parameters=execution.parameters,
            conversation_id=execution.conversation_id,
            context=execution.context
        )

        # Execute tool
        result = await tools_manager.execute_tool(
            str(current_user.id),
            tool_execution
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}"
        )


# ============================================================================
# Favorites Management
# ============================================================================

@router.get("/favorites", response_model=List[Dict[str, Any]])
async def get_favorite_tools(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Get user's favorite tools"""
    try:
        favorites = await tools_manager.get_favorites(
            str(current_user.id),
            current_user.role.value
        )

        favorite_list = []
        for tool in favorites:
            favorite_list.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "server_name": tool.server_name,
                "icon": tool.icon,
                "personal_data_risk": tool.personal_data_risk,
                "requires_parent_approval": tool.requires_parent_approval,
                "usage_count": tool.usage_count,
                "last_used": tool.last_used.isoformat() if tool.last_used else None
            })

        return favorite_list
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites: {str(e)}"
        )


@router.post("/favorites")
async def add_favorite_tool(
    favorite: FavoriteToolRequest,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Add tool to favorites"""
    try:
        success = await tools_manager.add_favorite(
            str(current_user.id),
            favorite.tool_name
        )

        if success:
            return {"message": f"Added '{favorite.tool_name}' to favorites"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add to favorites"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add favorite: {str(e)}"
        )


@router.delete("/favorites/{tool_name}")
async def remove_favorite_tool(
    tool_name: str,
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Remove tool from favorites"""
    try:
        success = await tools_manager.remove_favorite(
            str(current_user.id),
            tool_name
        )

        if success:
            return {"message": f"Removed '{tool_name}' from favorites"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found in favorites"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove favorite: {str(e)}"
        )


# ============================================================================
# Recommendations and Discovery
# ============================================================================

@router.get("/recommendations")
async def get_tool_recommendations(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Get personalized tool recommendations"""
    try:
        recommendations = await tools_manager.get_recommendations(
            str(current_user.id),
            current_user.role.value
        )

        return {
            "recommendations": recommendations,
            "message": "Based on your usage patterns and interests"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


# ============================================================================
# Usage History and Statistics
# ============================================================================

@router.get("/history")
async def get_usage_history(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager),
    days: int = Query(30, description="Number of days of history", ge=1, le=365)
):
    """Get tool usage history"""
    try:
        history = await tools_manager.get_usage_history(
            str(current_user.id),
            days
        )

        return {
            "history": history,
            "period_days": days,
            "total_executions": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager),
    days: int = Query(30, description="Number of days for stats", ge=1, le=365)
):
    """Get user's tool usage statistics"""
    try:
        history = await tools_manager.get_usage_history(
            str(current_user.id),
            days
        )

        favorites = await tools_manager.get_favorites(
            str(current_user.id),
            current_user.role.value
        )

        # Calculate statistics
        total_executions = len(history)
        successful_executions = len([h for h in history if h["success"]])
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0

        # Most used tools
        tool_counts = {}
        for execution in history:
            tool_name = execution["tool_name"]
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        top_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Average execution time
        execution_times = [h["execution_time_ms"] for h in history if h["execution_time_ms"]]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            "period_days": days,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "unique_tools_used": len(tool_counts),
            "favorite_tools_count": len(favorites),
            "top_tools": [
                {"tool_name": name, "usage_count": count}
                for name, count in top_tools
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


# ============================================================================
# Help and Information
# ============================================================================

@router.get("/help")
async def get_help_information():
    """Get help information for using family tools"""
    return {
        "title": "Family Tools Help Guide",
        "description": "Learn how to use tools to enhance your Family Assistant experience",
        "getting_started": [
            {
                "title": "Browse Available Tools",
                "description": "See all tools you can use",
                "how_to": "Go to Tools tab to see what's available for you"
            },
            {
                "title": "Use a Tool",
                "description": "Execute a tool with specific parameters",
                "how_to": "Select a tool and provide the required information"
            },
            {
                "title": "Save Favorites",
                "description": "Keep your most-used tools handy",
                "how_to": "Click the star icon on any tool to add it to favorites"
            }
        ],
        "popular_tools": [
            {
                "name": "Calendar Check",
                "description": "See today's schedule and appointments",
                "category": "calendar"
            },
            {
                "name": "Weather Forecast",
                "description": "Check the weather for today",
                "category": "weather"
            },
            {
                "name": "Quick Notes",
                "description": "Save quick notes and reminders",
                "category": "notes"
            },
            {
                "name": "Translation Helper",
                "description": "Translate words and phrases",
                "category": "education"
            }
        ],
        "safety_tips": [
            "Some tools may need parent approval before use",
            "Your tool usage is logged for family safety",
            "Personal data is protected and stays private",
            "Parents can monitor tool usage if needed"
        ],
        "examples": [
            {
                "tool": "Calendar Check",
                "request": "Check my calendar for today",
                "response": "You have math homework at 10 AM and soccer practice at 2 PM"
            },
            {
                "tool": "Quick Notes",
                "request": "Save a note: buy milk on way home",
                "response": "Note saved! You'll see a reminder later"
            },
            {
                "tool": "Weather Forecast",
                "request": "What's the weather like?",
                "response": "It's 72°F and partly cloudy today"
            }
        ]
    }


# ============================================================================
# Quick Actions
# ============================================================================

@router.get("/quick-actions")
async def get_quick_actions(
    current_user: FamilyMember = Depends(get_current_user_from_token),
    tools_manager: FamilyToolsManager = Depends(get_family_tools_manager)
):
    """Get quick action suggestions based on context"""
    try:
        tools = await tools_manager.get_available_tools(
            str(current_user.id),
            current_user.role.value
        )

        # Get recent usage for context
        history = await tools_manager.get_usage_history(str(current_user.id), 7)
        recent_tools = [h["tool_name"] for h in history[:3]]

        # Generate quick actions
        quick_actions = []

        # Always include weather
        weather_tool = next((t for t in tools if "weather" in t.name.lower()), None)
        if weather_tool:
            quick_actions.append({
                "tool_name": weather_tool.name,
                "action": "Check today's weather",
                "icon": weather_tool.icon,
                "category": weather_tool.category,
                "parameters": {}
            })

        # Add calendar if recently used
        calendar_tool = next((t for t in tools if "calendar" in t.name.lower()), None)
        if calendar_tool and any("calendar" in tool.lower() for tool in recent_tools):
            quick_actions.append({
                "tool_name": calendar_tool.name,
                "action": "Check today's schedule",
                "icon": calendar_tool.icon,
                "category": calendar_tool.category,
                "parameters": {}
            })

        # Add notes based on time of day
        note_tool = next((t for t in tools if "note" in t.name.lower() or "todo" in t.name.lower()), None)
        if note_tool:
            current_hour = datetime.now().hour
            if current_hour < 12:
                action = "Add morning note"
            elif current_hour < 17:
                action = "Add afternoon reminder"
            else:
                action = "Add evening note"

            quick_actions.append({
                "tool_name": note_tool.name,
                "action": action,
                "icon": note_tool.icon,
                "category": note_tool.category,
                "parameters": {}
            })

        # Add education tools for students
        if current_user.role in ["child", "teenager"]:
            edu_tools = [t for t in tools if t.category in ["education", "general"]]
            if edu_tools and len(quick_actions) < 4:
                edu_tool = edu_tools[0]
                quick_actions.append({
                    "tool_name": edu_tool.name,
                    "action": "Get homework help",
                    "icon": edu_tool.icon,
                    "category": edu_tool.category,
                    "parameters": {}
                })

        return {
            "quick_actions": quick_actions,
            "message": f"Hi {current_user.first_name}! Here are some tools you might find useful right now."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quick actions: {str(e)}"
        )