"""
Calendar Sub-Agent Implementation

Specialized agent for handling calendar and scheduling tasks in the Family Assistant.
This agent loads a specialized calendar management prompt and provides access to
calendar-specific MCP tools.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from sub_agents.base.base_agent import BaseSubAgent
from .tools import CalendarMCPTools

logger = logging.getLogger(__name__)


class CalendarSubAgent(BaseSubAgent):
    """
    Sub-agent specialized for calendar and scheduling operations.

    Capabilities:
    - Create, update, delete calendar events
    - Check for scheduling conflicts
    - Find available time slots
    - Manage recurring events
    - Coordinate family schedules
    """

    def __init__(self):
        # Load the skill prompt from the markdown file
        skill_prompt_path = Path(__file__).parent / "skill_prompt.md"
        with open(skill_prompt_path, 'r', encoding='utf-8') as f:
            skill_prompt = f.read()

        # Initialize with calendar-specific tools
        tools = [CalendarMCPTools()]

        super().__init__(
            agent_id="calendar",
            skill_prompt=skill_prompt,
            tools=tools,
            max_context=3000  # Keep context tight for local LLM efficiency
        )

    async def _execute_impl(
        self,
        request: str,
        user_context: Optional[Dict[str, Any]],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute calendar-specific task.

        This implementation uses a simple pattern-matching approach for the stub.
        In production, this would call an LLM with the skill_prompt to parse
        the request and determine which tools to call.
        """
        start_time = datetime.utcnow()
        tools_used = []

        try:
            # Simplified execution logic for stub
            # In production, this would:
            # 1. Call LLM with skill_prompt + request
            # 2. LLM decides which tools to call
            # 3. Execute tools via self.tools[0].execute_tool()
            # 4. Return synthesized response

            request_lower = request.lower()

            # Example: Create event
            if any(word in request_lower for word in ["schedule", "create", "add", "book"]):
                # Extract basic info (stub logic)
                result = await self.tools[0].execute_tool(
                    "calendar_create_event",
                    {
                        "title": "Event from request",
                        "start_time": "2025-01-15T14:00:00",
                        "end_time": "2025-01-15T15:00:00",
                        "attendees": [user_context.get("user_id", "unknown") if user_context else "unknown"]
                    }
                )
                tools_used.append("calendar_create_event")
                response = f"I've scheduled the event. Event ID: {result['result']['event_id']}"

            # Example: Check availability
            elif any(word in request_lower for word in ["available", "free", "when"]):
                result = await self.tools[0].execute_tool(
                    "calendar_get_availability",
                    {
                        "start_date": "2025-01-15",
                        "end_date": "2025-01-22",
                        "attendees": [user_context.get("user_id", "unknown") if user_context else "unknown"]
                    }
                )
                tools_used.append("calendar_get_availability")
                response = "Here are the available time slots I found..."

            # Example: List upcoming
            elif any(word in request_lower for word in ["upcoming", "next", "what's"]):
                result = await self.tools[0].execute_tool(
                    "calendar_list_upcoming",
                    {
                        "attendee": user_context.get("user_id", "unknown") if user_context else "unknown",
                        "days_ahead": 7
                    }
                )
                tools_used.append("calendar_list_upcoming")
                response = "Here are your upcoming events..."

            else:
                response = "I can help you with calendar tasks like scheduling, checking availability, or viewing upcoming events. What would you like to do?"

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return {
                "response": response,
                "tools_used": tools_used,
                "execution_time_ms": execution_time,
                "metadata": {
                    "request_type": "calendar",
                    "user_id": user_context.get("user_id") if user_context else None
                }
            }

        except Exception as e:
            logger.error(f"Calendar sub-agent execution error: {e}", exc_info=True)
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            return {
                "response": "I encountered an error while processing your calendar request.",
                "tools_used": tools_used,
                "execution_time_ms": execution_time,
                "metadata": {"error": str(e)}
            }
