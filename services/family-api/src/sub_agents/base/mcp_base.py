"""
MCP Tool Base Class

Provides abstraction layer for Model Context Protocol (MCP) tools used by sub-agents.
This class wraps tool definitions and execution logic, allowing sub-agents to call
tools without knowing implementation details.

Design:
- Each sub-agent has one or more MCPToolBase instances
- Tools are exposed via OpenAI-compatible function calling format
- Execution is async and returns structured results
"""

import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import inspect

logger = logging.getLogger(__name__)


class MCPToolBase(ABC):
    """
    Base class for MCP tool collections.

    Each sub-agent can have multiple MCPToolBase instances, each grouping
    related tools (e.g., CalendarMCPTools, HomeworkMCPTools).

    Subclasses must:
    1. Define TOOLS list with tool names
    2. Implement each tool as an async method
    3. Define get_tool_definitions() for function calling schema
    """

    def __init__(self, name: str, description: str = ""):
        """
        Initialize MCP tool base.

        Args:
            name: Unique tool collection name (e.g., "calendar_tools")
            description: Human-readable description of tool collection
        """
        self.name = name
        self.description = description
        self._initialized = False

        # Validate that all declared tools exist as methods
        self._validate_tools()

    def _validate_tools(self):
        """Ensure all tools in TOOLS list exist as async methods."""
        if not hasattr(self, 'TOOLS'):
            raise AttributeError(f"{self.__class__.__name__} must define TOOLS list")

        for tool_name in self.TOOLS:
            if not hasattr(self, tool_name):
                raise AttributeError(
                    f"{self.__class__.__name__} declares tool '{tool_name}' "
                    f"but method not found"
                )

            method = getattr(self, tool_name)
            if not inspect.iscoroutinefunction(method):
                raise TypeError(
                    f"Tool method '{tool_name}' must be async (coroutine)"
                )

    async def initialize(self):
        """Initialize tool resources (e.g., database connections, API clients)."""
        if self._initialized:
            return

        await self._init_impl()
        self._initialized = True
        logger.info(f"MCP tool collection '{self.name}' initialized")

    async def _init_impl(self):
        """Subclass-specific initialization. Override if needed."""
        pass

    @abstractmethod
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Return OpenAI-compatible function definitions for all tools.

        Format:
        [
            {
                "name": "tool_name",
                "description": "What the tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string", "description": "..."},
                        ...
                    },
                    "required": ["param1"]
                }
            }
        ]

        Returns:
            List of tool definition dicts
        """
        pass

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific tool by name.

        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters as dict

        Returns:
            Tool execution result dict

        Raises:
            ValueError: If tool_name not found
        """
        if tool_name not in self.TOOLS:
            raise ValueError(
                f"Tool '{tool_name}' not found in {self.name}. "
                f"Available: {self.TOOLS}"
            )

        method = getattr(self, tool_name)

        try:
            result = await method(**parameters)
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name
            }
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} tools={len(self.TOOLS)}>"
