"""
Unit tests for BaseSubAgent class
"""

import pytest
from typing import Dict, Any, Optional
from sub_agents.base.base_agent import BaseSubAgent
from sub_agents.base.mcp_base import MCPToolBase


class MockMCPTool(MCPToolBase):
    """Mock MCP tool for testing."""

    TOOLS = ["mock_tool_1", "mock_tool_2"]

    def __init__(self):
        super().__init__(name="mock_tools", description="Mock tools for testing")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "mock_tool_1",
                    "description": "Mock tool 1",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param1": {"type": "string"}
                        }
                    }
                }
            }
        ]

    async def mock_tool_1(self, param1: str = "default"):
        return {"result": f"mock_tool_1 executed with {param1}"}

    async def mock_tool_2(self):
        return {"result": "mock_tool_2 executed"}


class MockSubAgent(BaseSubAgent):
    """Mock sub-agent for testing."""

    def __init__(self):
        super().__init__(
            agent_id="mock_agent",
            skill_prompt="This is a mock agent for testing.",
            tools=[MockMCPTool()],
            max_context=1000
        )

    async def _execute_impl(
        self,
        request: str,
        user_context: Optional[Dict[str, Any]],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        return {
            "response": f"Mock response to: {request}",
            "tools_used": ["mock_tool_1"],
            "execution_time_ms": 10,
            "metadata": {"test": True}
        }


@pytest.mark.asyncio
async def test_base_agent_initialization():
    """Test BaseSubAgent initialization."""
    agent = MockSubAgent()

    assert agent.agent_id == "mock_agent"
    assert agent.max_context == 1000
    assert len(agent.tools) == 1
    assert "This is a mock agent" in agent.skill_prompt
    assert not agent._initialized


@pytest.mark.asyncio
async def test_base_agent_initialize():
    """Test BaseSubAgent async initialization."""
    agent = MockSubAgent()

    await agent.initialize()

    assert agent._initialized
    # Initialize is idempotent
    await agent.initialize()
    assert agent._initialized


@pytest.mark.asyncio
async def test_base_agent_execute():
    """Test BaseSubAgent execution."""
    agent = MockSubAgent()

    result = await agent.execute("Test request", {"user_id": "user123"}, "conv456")

    assert result["success"] is True
    assert result["agent_id"] == "mock_agent"
    assert "Mock response" in result["response"]
    assert "mock_tool_1" in result["tools_used"]
    assert result["execution_time_ms"] >= 0
    assert result["metadata"]["test"] is True


@pytest.mark.asyncio
async def test_base_agent_get_tool_definitions():
    """Test getting tool definitions from agent."""
    agent = MockSubAgent()

    definitions = agent.get_tool_definitions()

    assert len(definitions) > 0
    assert definitions[0]["type"] == "function"
    assert definitions[0]["function"]["name"] == "mock_tool_1"


@pytest.mark.asyncio
async def test_base_agent_get_available_tools():
    """Test getting available tool names."""
    agent = MockSubAgent()

    tools = agent.get_available_tools()

    assert "mock_tools" in tools


@pytest.mark.asyncio
async def test_base_agent_error_handling():
    """Test BaseSubAgent error handling."""

    class ErrorSubAgent(BaseSubAgent):
        def __init__(self):
            super().__init__(
                agent_id="error_agent",
                skill_prompt="Error agent",
                tools=[],
                max_context=1000
            )

        async def _execute_impl(self, request, user_context, conversation_id):
            raise ValueError("Intentional error")

    agent = ErrorSubAgent()
    result = await agent.execute("Test", None, None)

    assert result["success"] is False
    assert "error" in result["response"].lower()
    assert "Intentional error" in result["metadata"]["error"]


def test_base_agent_repr():
    """Test BaseSubAgent string representation."""
    agent = MockSubAgent()

    repr_str = repr(agent)

    assert "MockSubAgent" in repr_str
    assert "mock_agent" in repr_str
