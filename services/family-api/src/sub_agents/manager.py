"""
Sub-Agent Manager and Intent Classifier

Manages sub-agent lifecycle and routes requests to appropriate specialized agents
based on intent classification.

Architecture:
    User Request → IntentClassifier → SubAgentManager → Specific Sub-Agent → Tools
"""

import logging
import re
import time
import uuid
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

# Import Prometheus metrics tracking
from api.observability.metrics import (
    track_sub_agent_request,
    track_sub_agent_duration,
    track_sub_agent_tokens,
    track_sub_agent_tool_call
)

logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Represents a classified user intent."""
    agent_id: str
    confidence: float
    keywords: List[str]


class IntentClassifier:
    """
    Lightweight intent classifier for routing requests to sub-agents.

    Uses keyword-based pattern matching (100 tokens budget) to determine
    which sub-agent should handle a request.

    For production, this could be enhanced with:
    - Small classification model (e.g., distilbert fine-tuned)
    - Semantic similarity matching
    - User history-based prediction
    """

    # Intent patterns: agent_id → list of trigger keywords/phrases
    INTENT_PATTERNS = {
        "calendar": [
            # Scheduling keywords
            "schedule", "calendar", "appointment", "meeting", "event",
            # Time-related queries
            "when", "available", "free", "busy",
            # CRUD operations
            "book", "cancel", "reschedule", "move",
            # Event types
            "reminder", "dentist", "doctor", "practice", "game",
        ],
        # Future sub-agents can be added here:
        # "homework": ["homework", "assignment", "study", "test", "exam", ...],
        # "health": ["symptom", "medication", "doctor", "allergy", ...],
        # "shopping": ["buy", "grocery", "store", "shopping", "list", ...],
    }

    def __init__(self):
        """Initialize intent classifier."""
        self._compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Pre-compile regex patterns for efficiency."""
        compiled = {}
        for agent_id, keywords in self.INTENT_PATTERNS.items():
            # Create case-insensitive regex patterns
            patterns = [re.compile(rf'\b{re.escape(kw)}\b', re.IGNORECASE) for kw in keywords]
            compiled[agent_id] = patterns
        return compiled

    def classify(self, request: str) -> Optional[Intent]:
        """
        Classify user request to determine which sub-agent should handle it.

        Args:
            request: Natural language user request

        Returns:
            Intent object with agent_id and confidence, or None if no match
        """
        if not request or not request.strip():
            return None

        scores = {}
        matched_keywords = {}

        # Score each agent based on keyword matches
        for agent_id, patterns in self._compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(request):
                    matches.append(pattern.pattern[2:-2])  # Extract keyword from pattern

            if matches:
                # Simple scoring: count of matched keywords
                # Could be enhanced with TF-IDF, position weighting, etc.
                scores[agent_id] = len(matches)
                matched_keywords[agent_id] = matches

        if not scores:
            return None

        # Get best match
        best_agent = max(scores.keys(), key=lambda k: scores[k])
        max_score = scores[best_agent]
        total_keywords = len(self.INTENT_PATTERNS[best_agent])

        # Calculate confidence (0.0 to 1.0)
        confidence = min(max_score / 5.0, 1.0)  # Normalize by expected max matches

        logger.info(
            f"Intent classified: agent='{best_agent}', confidence={confidence:.2f}, "
            f"matched_keywords={matched_keywords[best_agent]}"
        )

        return Intent(
            agent_id=best_agent,
            confidence=confidence,
            keywords=matched_keywords[best_agent]
        )

    def add_intent(self, agent_id: str, keywords: List[str]) -> None:
        """
        Dynamically add or update intent patterns for a new sub-agent.

        Args:
            agent_id: Unique agent identifier
            keywords: List of trigger keywords
        """
        self.INTENT_PATTERNS[agent_id] = keywords
        self._compiled_patterns = self._compile_patterns()
        logger.info(f"Added intent pattern for agent '{agent_id}' with {len(keywords)} keywords")


class SubAgentManager:
    """
    Manages sub-agent lifecycle and request routing.

    Responsibilities:
    1. Register and maintain sub-agent instances
    2. Route requests based on intent classification
    3. Handle sub-agent initialization and cleanup
    4. Expose sub-agent capabilities to orchestrator
    """

    def __init__(self):
        """Initialize sub-agent manager."""
        self.agents: Dict[str, Any] = {}  # agent_id → BaseSubAgent instance
        self.intent_classifier = IntentClassifier()
        self._initialized = False

    async def initialize(self):
        """Initialize all registered sub-agents."""
        if self._initialized:
            return

        logger.info(f"Initializing SubAgentManager with {len(self.agents)} agents")

        for agent_id, agent in self.agents.items():
            try:
                await agent.initialize()
                logger.info(f"Sub-agent '{agent_id}' initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize sub-agent '{agent_id}': {e}", exc_info=True)

        self._initialized = True
        logger.info("SubAgentManager initialization complete")

    def register_agent(self, agent: Any) -> None:
        """
        Register a new sub-agent.

        Args:
            agent: BaseSubAgent instance to register

        Raises:
            ValueError: If agent_id already registered
        """
        if agent.agent_id in self.agents:
            raise ValueError(f"Agent '{agent.agent_id}' already registered")

        self.agents[agent.agent_id] = agent
        logger.info(f"Registered sub-agent: {agent.agent_id}")

    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister a sub-agent.

        Args:
            agent_id: Agent identifier to remove
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered sub-agent: {agent_id}")

    async def route_request(
        self,
        request: str,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        force_agent: Optional[str] = None,
        db_pool: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Route a request to the appropriate sub-agent.

        Args:
            request: Natural language request
            user_context: Optional user profile/preferences
            conversation_id: Optional conversation tracking ID
            force_agent: Optional agent_id to force routing (bypasses classification)
            db_pool: Optional database connection pool for analytics

        Returns:
            Dict containing sub-agent response and metadata
        """
        if not self._initialized:
            await self.initialize()

        # Generate execution_id for tracking
        execution_id = uuid.uuid4()
        start_time = time.time()

        # Track intent classification timing
        intent_start = time.time()

        # Determine which agent to use
        if force_agent:
            agent_id = force_agent
            intent = None
            intent_duration_ms = 0
        else:
            intent = self.intent_classifier.classify(request)
            intent_duration_ms = int((time.time() - intent_start) * 1000)

            if not intent:
                return {
                    "success": False,
                    "error": "No suitable sub-agent found for request",
                    "request": request,
                    "execution_id": str(execution_id)
                }
            agent_id = intent.agent_id

        # Validate agent exists
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Sub-agent '{agent_id}' not found",
                "available_agents": list(self.agents.keys()),
                "execution_id": str(execution_id)
            }

        # Execute via sub-agent
        agent = self.agents[agent_id]
        result = await agent.execute(request, user_context, conversation_id)

        # Calculate total duration
        total_duration_ms = int((time.time() - start_time) * 1000)

        # Add routing metadata
        result["intent"] = {
            "agent_id": intent.agent_id if intent else agent_id,
            "confidence": intent.confidence if intent else 1.0,
            "matched_keywords": intent.keywords if intent else []
        }

        # Add execution tracking
        result["execution_id"] = str(execution_id)
        result["total_duration_ms"] = total_duration_ms

        # Track Prometheus metrics
        try:
            # Track request completion
            track_sub_agent_request(agent_id, result.get("success", False))

            # Track timing metrics (convert ms to seconds for Prometheus)
            track_sub_agent_duration(agent_id, "intent", intent_duration_ms / 1000.0)
            track_sub_agent_duration(agent_id, "agent", result.get("execution_time_ms", 0) / 1000.0)
            track_sub_agent_duration(agent_id, "total", total_duration_ms / 1000.0)

            # Track token usage
            instrumentation = result.get("instrumentation", {})
            if instrumentation:
                track_sub_agent_tokens(
                    agent_id,
                    prompt_tokens=instrumentation.get("prompt_tokens") or 0,
                    completion_tokens=instrumentation.get("completion_tokens") or 0,
                    skill_prompt_tokens=instrumentation.get("skill_prompt_tokens") or 0
                )

                # Track tool calls
                for tool_call in instrumentation.get("tool_calls", []):
                    track_sub_agent_tool_call(
                        agent_id,
                        tool_call.get("tool_name", "unknown"),
                        tool_call.get("success", False)
                    )
        except Exception as e:
            logger.error(f"Failed to track Prometheus metrics: {e}", exc_info=True)

        # Store execution trace in database if pool provided
        if db_pool and result.get("success", False):
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO sub_agent_executions (
                            execution_id, user_id, conversation_id, request_text,
                            agent_id, confidence, keywords, intent_duration_ms,
                            skill_prompt_size, skill_prompt_tokens, agent_duration_ms,
                            total_tokens, prompt_tokens, completion_tokens,
                            total_duration_ms, success, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """,
                        execution_id,
                        user_context.get("user_id") if user_context else None,
                        conversation_id,
                        request,
                        agent_id,
                        intent.confidence if intent else 1.0,
                        intent.keywords if intent else [],
                        intent_duration_ms,
                        result.get("instrumentation", {}).get("skill_prompt_size"),
                        result.get("instrumentation", {}).get("skill_prompt_tokens"),
                        result.get("execution_time_ms", 0),
                        result.get("instrumentation", {}).get("total_tokens"),
                        result.get("instrumentation", {}).get("prompt_tokens"),
                        result.get("instrumentation", {}).get("completion_tokens"),
                        total_duration_ms,
                        result.get("success", True),
                        result.get("metadata", {})
                    )

                    # Store tool calls if present
                    tool_calls = result.get("instrumentation", {}).get("tool_calls", [])
                    for idx, tool_call in enumerate(tool_calls):
                        await conn.execute("""
                            INSERT INTO sub_agent_tool_calls (
                                execution_id, tool_name, agent_id, call_index,
                                parameters, result, duration_ms, success
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """,
                            execution_id,
                            tool_call.get("tool_name"),
                            agent_id,
                            idx,
                            tool_call.get("parameters", {}),
                            tool_call.get("result", {}),
                            tool_call.get("duration_ms", 0),
                            tool_call.get("success", True)
                        )

            except Exception as e:
                logger.error(f"Failed to store execution trace: {e}", exc_info=True)

        return result

    def get_available_agents(self) -> List[str]:
        """Get list of registered agent IDs."""
        return list(self.agents.keys())

    def get_agent_tools(self, agent_id: str) -> Optional[List[str]]:
        """Get list of tools available to a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        return agent.get_available_tools()

    def get_all_tool_definitions(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tool definitions from all registered agents.

        Returns:
            Dict mapping agent_id → list of tool definitions
        """
        return {
            agent_id: agent.get_tool_definitions()
            for agent_id, agent in self.agents.items()
        }

    def __repr__(self) -> str:
        return f"<SubAgentManager agents={list(self.agents.keys())}>"


# Global singleton instance (initialized in startup)
_manager: Optional[SubAgentManager] = None


def get_sub_agent_manager() -> SubAgentManager:
    """
    Get the global SubAgentManager instance.

    Returns:
        Initialized SubAgentManager singleton
    """
    global _manager
    if _manager is None:
        _manager = SubAgentManager()

        # Register sub-agents here
        from sub_agents.calendar import CalendarSubAgent
        _manager.register_agent(CalendarSubAgent())

        # Future agents:
        # from sub_agents.homework import HomeworkSubAgent
        # _manager.register_agent(HomeworkSubAgent())

    return _manager


async def initialize_sub_agent_system():
    """Initialize the sub-agent system during app startup."""
    manager = get_sub_agent_manager()
    await manager.initialize()
    logger.info("Sub-agent system initialized")
