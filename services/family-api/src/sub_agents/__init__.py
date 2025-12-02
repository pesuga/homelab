"""
Sub-Agent Architecture for Family Assistant

This package implements the Orchestrator-Worker pattern where the main agent
retains personality and delegates specialized tasks to sub-agents via MCP tools.

Architecture:
    Main Agent (Orchestrator) → Sub-Agent (Worker) → Specific MCP Tools

Sub-agents are ephemeral, loaded just-in-time with their specialized prompts,
execute their task, and return results to the orchestrator without polluting
the main agent's context.
"""

from .base.base_agent import BaseSubAgent
from .base.mcp_base import MCPToolBase
from .manager import SubAgentManager, IntentClassifier

__all__ = [
    "BaseSubAgent",
    "MCPToolBase",
    "SubAgentManager",
    "IntentClassifier",
]
