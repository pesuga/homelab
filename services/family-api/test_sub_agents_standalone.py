#!/usr/bin/env python3
"""
Standalone test script for sub-agent implementation.
Run this to verify the sub-agent architecture works correctly.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sub_agents.base.base_agent import BaseSubAgent
from sub_agents.base.mcp_base import MCPToolBase
from sub_agents.calendar import CalendarSubAgent, CalendarMCPTools
from sub_agents.manager import SubAgentManager, IntentClassifier


def test_base_classes():
    """Test base class instantiation."""
    print("✓ Testing base classes...")

    # Test MCPToolBase
    tools = CalendarMCPTools()
    assert tools.name == "calendar_tools"
    assert len(tools.TOOLS) == 7
    print(f"  ✓ CalendarMCPTools initialized with {len(tools.TOOLS)} tools")

    # Test tool definitions
    definitions = tools.get_tool_definitions()
    assert len(definitions) == 7
    assert definitions[0]["type"] == "function"
    print(f"  ✓ Tool definitions validated")


async def test_calendar_agent():
    """Test calendar sub-agent."""
    print("\n✓ Testing Calendar Sub-Agent...")

    agent = CalendarSubAgent()
    assert agent.agent_id == "calendar"
    assert agent.max_context == 3000
    print(f"  ✓ Agent initialized: {agent.agent_id}")

    # Test skill prompt loading
    assert len(agent.skill_prompt) > 100
    assert "calendar" in agent.skill_prompt.lower()
    print(f"  ✓ Skill prompt loaded: {len(agent.skill_prompt)} chars")

    # Test execution
    result = await agent.execute(
        "Schedule a meeting tomorrow at 2pm",
        {"user_id": "user123"},
        "conv456"
    )

    assert result["success"] is True
    assert result["agent_id"] == "calendar"
    assert len(result["tools_used"]) > 0
    print(f"  ✓ Execution successful: {result['tools_used']}")


async def test_calendar_tools():
    """Test calendar MCP tools."""
    print("\n✓ Testing Calendar Tools...")

    tools = CalendarMCPTools()
    await tools.initialize()

    # Test create event
    result = await tools.calendar_create_event(
        title="Test Meeting",
        start_time="2025-01-15T14:00:00",
        end_time="2025-01-15T15:00:00",
        attendees=["user1", "user2"]
    )

    assert "event_id" in result
    assert result["status"] == "confirmed"
    print(f"  ✓ create_event: {result['event_id']}")

    # Test search events
    result = await tools.calendar_search_events(
        start_date="2025-01-01",
        end_date="2025-01-31"
    )

    assert "events" in result
    assert "total_found" in result
    print(f"  ✓ search_events: {result['total_found']} events")

    # Test via execute_tool
    result = await tools.execute_tool(
        "calendar_check_conflicts",
        {
            "start_time": "2025-01-15T10:00:00",
            "end_time": "2025-01-15T11:00:00",
            "attendees": ["user1"]
        }
    )

    assert result["success"] is True
    assert "has_conflicts" in result["result"]
    print(f"  ✓ check_conflicts: {result['result']['has_conflicts']}")


def test_intent_classifier():
    """Test intent classification."""
    print("\n✓ Testing Intent Classifier...")

    classifier = IntentClassifier()

    # Test calendar intents
    test_cases = [
        ("Schedule a meeting tomorrow", "calendar"),
        ("Check my calendar", "calendar"),
        ("When am I free?", "calendar"),
        ("Book an appointment", "calendar"),
    ]

    for request, expected_agent in test_cases:
        intent = classifier.classify(request)
        assert intent is not None, f"No intent for: {request}"
        assert intent.agent_id == expected_agent, f"Wrong agent for: {request}"
        assert intent.confidence > 0.0
        print(f"  ✓ '{request}' → {intent.agent_id} ({intent.confidence:.2f})")

    # Test no match
    intent = classifier.classify("Tell me a joke")
    assert intent is None
    print(f"  ✓ No match for unrelated request")


async def test_sub_agent_manager():
    """Test SubAgentManager."""
    print("\n✓ Testing SubAgentManager...")

    manager = SubAgentManager()

    # Register agent
    agent = CalendarSubAgent()
    manager.register_agent(agent)
    assert "calendar" in manager.agents
    print(f"  ✓ Agent registered: {list(manager.agents.keys())}")

    # Initialize
    await manager.initialize()
    assert manager._initialized
    print(f"  ✓ Manager initialized")

    # Test routing with classification
    result = await manager.route_request(
        "Schedule a dentist appointment tomorrow at 2pm",
        {"user_id": "user123"},
        "conv456"
    )

    assert result["success"] is True
    assert result["agent_id"] == "calendar"
    assert "intent" in result
    assert result["intent"]["agent_id"] == "calendar"
    print(f"  ✓ Routing successful: {result['agent_id']} (confidence: {result['intent']['confidence']:.2f})")

    # Test forced routing
    result = await manager.route_request(
        "Some random request",
        None,
        None,
        force_agent="calendar"
    )

    assert result["success"] is True
    assert result["agent_id"] == "calendar"
    print(f"  ✓ Forced routing successful")

    # Test tools listing
    tools = manager.get_agent_tools("calendar")
    assert tools is not None
    assert len(tools) > 0
    print(f"  ✓ Agent tools: {tools}")


async def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Sub-Agent Architecture Test Suite")
    print("="*60)

    try:
        # Synchronous tests
        test_base_classes()
        test_intent_classifier()

        # Async tests
        await test_calendar_agent()
        await test_calendar_tools()
        await test_sub_agent_manager()

        print("\n" + "="*60)
        print("✅ All tests passed!")
        print("="*60)
        return True

    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ Test failed: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
