"""
Unit tests for Calendar Sub-Agent
"""

import pytest
from pathlib import Path
from sub_agents.calendar import CalendarSubAgent, CalendarMCPTools


@pytest.mark.asyncio
async def test_calendar_agent_initialization():
    """Test CalendarSubAgent initialization."""
    agent = CalendarSubAgent()

    assert agent.agent_id == "calendar"
    assert agent.max_context == 3000
    assert len(agent.tools) == 1
    assert isinstance(agent.tools[0], CalendarMCPTools)
    assert len(agent.skill_prompt) > 100  # Has substantial prompt


@pytest.mark.asyncio
async def test_calendar_agent_skill_prompt_loaded():
    """Test that skill prompt is loaded from file."""
    agent = CalendarSubAgent()

    assert "calendar" in agent.skill_prompt.lower()
    assert "schedule" in agent.skill_prompt.lower()
    # Check for key sections from the prompt
    assert "Core Capabilities" in agent.skill_prompt
    assert "Available Tools" in agent.skill_prompt


@pytest.mark.asyncio
async def test_calendar_tools_initialization():
    """Test CalendarMCPTools initialization."""
    tools = CalendarMCPTools()

    assert tools.name == "calendar_tools"
    assert len(tools.TOOLS) == 7
    assert "calendar_create_event" in tools.TOOLS
    assert "calendar_search_events" in tools.TOOLS
    assert "calendar_check_conflicts" in tools.TOOLS


@pytest.mark.asyncio
async def test_calendar_tool_definitions():
    """Test calendar tool definitions format."""
    tools = CalendarMCPTools()

    definitions = tools.get_tool_definitions()

    assert len(definitions) == 7
    # Validate first tool structure
    create_event_def = definitions[0]
    assert create_event_def["type"] == "function"
    assert create_event_def["function"]["name"] == "calendar_create_event"
    assert "parameters" in create_event_def["function"]
    assert "title" in create_event_def["function"]["parameters"]["properties"]
    assert "start_time" in create_event_def["function"]["parameters"]["properties"]


@pytest.mark.asyncio
async def test_calendar_create_event():
    """Test calendar_create_event tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_create_event(
        title="Test Event",
        start_time="2025-01-15T10:00:00",
        end_time="2025-01-15T11:00:00",
        attendees=["user1", "user2"],
        location="Office",
        description="Test description"
    )

    assert "event_id" in result
    assert result["title"] == "Test Event"
    assert result["status"] == "confirmed"
    assert len(result["attendees"]) == 2
    assert result["location"] == "Office"


@pytest.mark.asyncio
async def test_calendar_search_events():
    """Test calendar_search_events tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_search_events(
        start_date="2025-01-01",
        end_date="2025-01-31"
    )

    assert "events" in result
    assert "total_found" in result
    assert isinstance(result["events"], list)


@pytest.mark.asyncio
async def test_calendar_check_conflicts():
    """Test calendar_check_conflicts tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_check_conflicts(
        start_time="2025-01-15T14:00:00",
        end_time="2025-01-15T15:00:00",
        attendees=["user1"]
    )

    assert "has_conflicts" in result
    assert "conflicts" in result
    assert "available" in result
    assert isinstance(result["has_conflicts"], bool)


@pytest.mark.asyncio
async def test_calendar_get_availability():
    """Test calendar_get_availability tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_get_availability(
        start_date="2025-01-15",
        end_date="2025-01-22",
        attendees=["user1", "user2"],
        min_duration_minutes=60
    )

    assert "free_slots" in result
    assert "attendees" in result
    assert isinstance(result["free_slots"], list)
    assert result["attendees"] == ["user1", "user2"]


@pytest.mark.asyncio
async def test_calendar_update_event():
    """Test calendar_update_event tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_update_event(
        event_id="evt_123",
        updates={"title": "Updated Event", "location": "New Location"}
    )

    assert result["event_id"] == "evt_123"
    assert result["status"] == "updated"
    assert "updated_at" in result
    assert result["updates_applied"]["title"] == "Updated Event"


@pytest.mark.asyncio
async def test_calendar_delete_event():
    """Test calendar_delete_event tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_delete_event(event_id="evt_456")

    assert result["event_id"] == "evt_456"
    assert result["status"] == "deleted"
    assert "deleted_at" in result


@pytest.mark.asyncio
async def test_calendar_list_upcoming():
    """Test calendar_list_upcoming tool."""
    tools = CalendarMCPTools()

    result = await tools.calendar_list_upcoming(
        attendee="user1",
        days_ahead=7,
        limit=10
    )

    assert "events" in result
    assert "attendee" in result
    assert "total_events" in result
    assert result["attendee"] == "user1"


@pytest.mark.asyncio
async def test_calendar_agent_execute_create():
    """Test calendar agent execution for create request."""
    agent = CalendarSubAgent()

    result = await agent.execute(
        "Schedule a dentist appointment tomorrow at 2pm",
        {"user_id": "user123"},
        "conv456"
    )

    assert result["success"] is True
    assert result["agent_id"] == "calendar"
    assert "event" in result["response"].lower() or "scheduled" in result["response"].lower()
    assert "calendar_create_event" in result["tools_used"]


@pytest.mark.asyncio
async def test_calendar_agent_execute_availability():
    """Test calendar agent execution for availability request."""
    agent = CalendarSubAgent()

    result = await agent.execute(
        "When am I free this week?",
        {"user_id": "user123"},
        None
    )

    assert result["success"] is True
    assert "calendar_get_availability" in result["tools_used"]


@pytest.mark.asyncio
async def test_calendar_agent_execute_upcoming():
    """Test calendar agent execution for upcoming events."""
    agent = CalendarSubAgent()

    result = await agent.execute(
        "What's on my calendar next week?",
        {"user_id": "user123"},
        None
    )

    assert result["success"] is True
    assert "calendar_list_upcoming" in result["tools_used"]


@pytest.mark.asyncio
async def test_calendar_agent_tool_execution():
    """Test that calendar tools can be executed via agent."""
    agent = CalendarSubAgent()
    await agent.initialize()

    tools = agent.tools[0]
    result = await tools.execute_tool(
        "calendar_create_event",
        {
            "title": "Team Meeting",
            "start_time": "2025-01-16T10:00:00",
            "end_time": "2025-01-16T11:00:00",
            "attendees": ["user1"]
        }
    )

    assert result["success"] is True
    assert "event_id" in result["result"]
