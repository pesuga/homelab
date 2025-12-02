"""
Base Sub-Agent Class

Implements the foundation for all specialized sub-agents in the orchestrator-worker pattern.
Sub-agents are ephemeral workers that load specialized prompts just-in-time, execute tasks,
and return concise results to the main orchestrator agent.

Key Design Principles:
1. Token Efficiency: Sub-agents load heavy prompts (5-10K tokens) only when needed
2. Isolation: Each sub-agent is self-contained with its own tools and context
3. Stateless: Sub-agents don't maintain conversation history (orchestrator does)
4. MCP Integration: Tools exposed via MCP protocol for clean abstraction
"""

import logging
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSubAgent(ABC):
    """
    Base class for all sub-agents in the Family Assistant system.

    Sub-agents are specialized workers that:
    - Handle specific domain tasks (calendar, homework, health, etc.)
    - Load domain-specific prompts ephemerally
    - Execute via MCP tools
    - Return concise summaries to the orchestrator

    Attributes:
        agent_id: Unique identifier for this sub-agent
        skill_prompt: Domain-specific system prompt (5-10K tokens)
        tools: List of MCPToolBase instances for this agent
        max_context: Maximum context window for local LLM efficiency
    """

    def __init__(
        self,
        agent_id: str,
        skill_prompt: str,
        tools: List["MCPToolBase"],
        max_context: int = 3000
    ):
        """
        Initialize a sub-agent.

        Args:
            agent_id: Unique identifier (e.g., "calendar", "homework")
            skill_prompt: Complete system prompt loaded from skill_prompt.md
            tools: List of MCP tool instances available to this agent
            max_context: Token limit for context window (default: 3000 for local LLMs)
        """
        self.agent_id = agent_id
        self.skill_prompt = skill_prompt
        self.tools = tools
        self.max_context = max_context
        self._initialized = False

        logger.info(
            f"Sub-agent '{agent_id}' initialized with {len(tools)} tools, "
            f"max_context={max_context} tokens"
        )

    async def initialize(self) -> None:
        """
        Async initialization for sub-agent (e.g., load external resources).
        Called lazily on first use.
        """
        if self._initialized:
            return

        # Initialize all tools
        for tool in self.tools:
            await tool.initialize()

        self._initialized = True
        logger.info(f"Sub-agent '{self.agent_id}' fully initialized")

    async def execute(
        self,
        request: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task request using this sub-agent.

        This is the main entry point called by the orchestrator. The sub-agent:
        1. Loads its specialized prompt
        2. Processes the request using available tools
        3. Returns a concise summary to the orchestrator

        Args:
            request: Natural language request from orchestrator
            user_context: Optional user profile/preferences
            conversation_id: Optional conversation tracking ID

        Returns:
            Dict containing:
                - response: String response to return to orchestrator
                - tools_used: List of tools executed
                - execution_time_ms: Time taken
                - metadata: Additional context
                - instrumentation: Performance and token metrics
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Calculate skill prompt metadata
            skill_prompt_size = len(self.skill_prompt.encode('utf-8'))
            # Rough token estimation (1 token ≈ 4 characters)
            skill_prompt_tokens = len(self.skill_prompt) // 4

            # Delegate to subclass implementation
            result = await self._execute_impl(request, user_context, conversation_id)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Build instrumentation data
            instrumentation = {
                "skill_prompt_size": skill_prompt_size,
                "skill_prompt_tokens": skill_prompt_tokens,
                "agent_execution_time_ms": execution_time_ms,
                "total_tokens": result.get("total_tokens"),
                "prompt_tokens": result.get("prompt_tokens"),
                "completion_tokens": result.get("completion_tokens"),
                "tool_calls": result.get("tool_calls", [])
            }

            # Ensure standard response format
            return {
                "agent_id": self.agent_id,
                "response": result.get("response", ""),
                "tools_used": result.get("tools_used", []),
                "execution_time_ms": execution_time_ms,
                "metadata": result.get("metadata", {}),
                "instrumentation": instrumentation,
                "success": True
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Sub-agent '{self.agent_id}' execution failed: {e}", exc_info=True)
            return {
                "agent_id": self.agent_id,
                "response": f"I encountered an error while processing your {self.agent_id} request.",
                "tools_used": [],
                "execution_time_ms": execution_time_ms,
                "metadata": {"error": str(e)},
                "instrumentation": {
                    "skill_prompt_size": len(self.skill_prompt.encode('utf-8')),
                    "skill_prompt_tokens": len(self.skill_prompt) // 4,
                    "agent_execution_time_ms": execution_time_ms,
                    "error": True
                },
                "success": False
            }

    @abstractmethod
    async def _execute_impl(
        self,
        request: str,
        user_context: Optional[Dict[str, Any]],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Subclass-specific implementation of task execution.

        This method should:
        1. Parse the request
        2. Call appropriate MCP tools
        3. Synthesize results into a concise response

        Returns:
            Dict with keys: response, tools_used, execution_time_ms, metadata
        """
        pass

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool definitions for this sub-agent's tools.

        Returns:
            List of tool definition dicts for function calling
        """
        definitions = []
        for tool in self.tools:
            definitions.extend(tool.get_tool_definitions())
        return definitions

    def get_available_tools(self) -> List[str]:
        """Get list of tool names available to this sub-agent."""
        return [tool.name for tool in self.tools]

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"id='{self.agent_id}' "
            f"tools={len(self.tools)} "
            f"max_context={self.max_context}>"
        )
