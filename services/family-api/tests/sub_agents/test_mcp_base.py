"""
Unit tests for MCPToolBase class
"""

import pytest
from sub_agents.base.mcp_base import MCPToolBase


class TestMCPTool(MCPToolBase):
    """Test MCP tool implementation."""

    TOOLS = ["test_tool_1", "test_tool_2"]

    def __init__(self):
        super().__init__(name="test_tools", description="Test tools")

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "test_tool_1",
                    "description": "Test tool 1",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input": {"type": "string"}
                        },
                        "required": ["input"]
                    }
                }
            }
        ]

    async def test_tool_1(self, input: str):
        return {"output": f"processed: {input}"}

    async def test_tool_2(self):
        return {"status": "ok"}


@pytest.mark.asyncio
async def test_mcp_tool_initialization():
    """Test MCPToolBase initialization."""
    tool = TestMCPTool()

    assert tool.name == "test_tools"
    assert tool.description == "Test tools"
    assert not tool._initialized
    assert hasattr(tool, 'TOOLS')
    assert len(tool.TOOLS) == 2


@pytest.mark.asyncio
async def test_mcp_tool_validate_tools():
    """Test tool validation during initialization."""
    # Should not raise - all tools exist
    tool = TestMCPTool()
    assert len(tool.TOOLS) == 2


@pytest.mark.asyncio
async def test_mcp_tool_missing_method():
    """Test validation fails when tool method missing."""

    class InvalidTool(MCPToolBase):
        TOOLS = ["missing_tool"]

        def __init__(self):
            super().__init__(name="invalid")

        def get_tool_definitions(self):
            return []

    with pytest.raises(AttributeError, match="method not found"):
        InvalidTool()


@pytest.mark.asyncio
async def test_mcp_tool_non_async_method():
    """Test validation fails when tool method is not async."""

    class NonAsyncTool(MCPToolBase):
        TOOLS = ["sync_tool"]

        def __init__(self):
            super().__init__(name="non_async")

        def get_tool_definitions(self):
            return []

        def sync_tool(self):  # Not async!
            return {}

    with pytest.raises(TypeError, match="must be async"):
        NonAsyncTool()


@pytest.mark.asyncio
async def test_mcp_tool_initialize():
    """Test MCPToolBase initialization."""
    tool = TestMCPTool()

    await tool.initialize()

    assert tool._initialized
    # Idempotent
    await tool.initialize()
    assert tool._initialized


@pytest.mark.asyncio
async def test_mcp_tool_execute():
    """Test executing a tool."""
    tool = TestMCPTool()

    result = await tool.execute_tool("test_tool_1", {"input": "hello"})

    assert result["success"] is True
    assert result["tool_name"] == "test_tool_1"
    assert result["result"]["output"] == "processed: hello"


@pytest.mark.asyncio
async def test_mcp_tool_execute_invalid():
    """Test executing invalid tool name."""
    tool = TestMCPTool()

    with pytest.raises(ValueError, match="not found"):
        await tool.execute_tool("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_mcp_tool_execute_error():
    """Test tool execution error handling."""

    class ErrorTool(MCPToolBase):
        TOOLS = ["error_tool"]

        def __init__(self):
            super().__init__(name="error_tools")

        def get_tool_definitions(self):
            return []

        async def error_tool(self):
            raise RuntimeError("Tool error")

    tool = ErrorTool()
    result = await tool.execute_tool("error_tool", {})

    assert result["success"] is False
    assert "Tool error" in result["error"]
    assert result["tool_name"] == "error_tool"


def test_mcp_tool_repr():
    """Test MCPToolBase string representation."""
    tool = TestMCPTool()

    repr_str = repr(tool)

    assert "TestMCPTool" in repr_str
    assert "tools=2" in repr_str
