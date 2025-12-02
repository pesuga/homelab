"""
Unit tests for SubAgentManager and IntentClassifier
"""

import pytest
from sub_agents.manager import SubAgentManager, IntentClassifier, Intent
from sub_agents.calendar import CalendarSubAgent


class TestIntentClassifier:
    """Tests for IntentClassifier."""

    def test_classifier_initialization(self):
        """Test intent classifier initialization."""
        classifier = IntentClassifier()

        assert "calendar" in classifier.INTENT_PATTERNS
        assert len(classifier.INTENT_PATTERNS["calendar"]) > 0
        assert len(classifier._compiled_patterns) > 0

    def test_classify_calendar_intent(self):
        """Test classifying calendar-related requests."""
        classifier = IntentClassifier()

        # Test various calendar keywords
        test_cases = [
            "Schedule a meeting tomorrow",
            "Check my calendar for next week",
            "Book a dentist appointment",
            "When am I free?",
            "Cancel my 3pm meeting"
        ]

        for request in test_cases:
            intent = classifier.classify(request)
            assert intent is not None
            assert intent.agent_id == "calendar"
            assert intent.confidence > 0.0
            assert len(intent.keywords) > 0

    def test_classify_no_match(self):
        """Test classifying request with no matching intent."""
        classifier = IntentClassifier()

        intent = classifier.classify("Tell me a joke")

        # Should return None when no agent matches
        assert intent is None

    def test_classify_empty_request(self):
        """Test classifying empty request."""
        classifier = IntentClassifier()

        intent = classifier.classify("")
        assert intent is None

        intent = classifier.classify("   ")
        assert intent is None

    def test_add_intent_dynamically(self):
        """Test dynamically adding new intent patterns."""
        classifier = IntentClassifier()

        classifier.add_intent("homework", ["homework", "assignment", "study", "test"])

        assert "homework" in classifier.INTENT_PATTERNS
        assert "homework" in classifier._compiled_patterns

        # Test classification with new intent
        intent = classifier.classify("Help me with my homework")
        assert intent is not None
        assert intent.agent_id == "homework"

    def test_confidence_scoring(self):
        """Test confidence scoring based on keyword matches."""
        classifier = IntentClassifier()

        # More keywords = higher confidence
        low_confidence = classifier.classify("schedule something")
        high_confidence = classifier.classify("schedule a calendar appointment meeting event")

        assert low_confidence.confidence < high_confidence.confidence


class TestSubAgentManager:
    """Tests for SubAgentManager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test sub-agent manager initialization."""
        manager = SubAgentManager()

        assert len(manager.agents) == 0
        assert not manager._initialized
        assert isinstance(manager.intent_classifier, IntentClassifier)

    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Test registering a sub-agent."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()

        manager.register_agent(agent)

        assert "calendar" in manager.agents
        assert manager.agents["calendar"] == agent

    @pytest.mark.asyncio
    async def test_register_duplicate_agent(self):
        """Test registering duplicate agent raises error."""
        manager = SubAgentManager()
        agent1 = CalendarSubAgent()
        agent2 = CalendarSubAgent()

        manager.register_agent(agent1)

        with pytest.raises(ValueError, match="already registered"):
            manager.register_agent(agent2)

    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Test unregistering a sub-agent."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()

        manager.register_agent(agent)
        assert "calendar" in manager.agents

        manager.unregister_agent("calendar")
        assert "calendar" not in manager.agents

    @pytest.mark.asyncio
    async def test_initialize_manager(self):
        """Test manager initialization."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        await manager.initialize()

        assert manager._initialized
        # Idempotent
        await manager.initialize()
        assert manager._initialized

    @pytest.mark.asyncio
    async def test_route_request_with_classification(self):
        """Test routing request via intent classification."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        result = await manager.route_request(
            "Schedule a meeting tomorrow",
            {"user_id": "user123"},
            "conv456"
        )

        assert result["success"] is True
        assert result["agent_id"] == "calendar"
        assert "intent" in result
        assert result["intent"]["agent_id"] == "calendar"
        assert result["intent"]["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_route_request_force_agent(self):
        """Test routing request with forced agent."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        result = await manager.route_request(
            "This doesn't match any pattern",
            None,
            None,
            force_agent="calendar"
        )

        assert result["success"] is True
        assert result["agent_id"] == "calendar"

    @pytest.mark.asyncio
    async def test_route_request_no_match(self):
        """Test routing request with no matching agent."""
        manager = SubAgentManager()
        # No agents registered

        result = await manager.route_request("Tell me a joke", None, None)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_route_request_invalid_agent(self):
        """Test routing request to non-existent agent."""
        manager = SubAgentManager()

        result = await manager.route_request(
            "Test request",
            None,
            None,
            force_agent="nonexistent"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_available_agents(self):
        """Test getting list of available agents."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        agents = manager.get_available_agents()

        assert "calendar" in agents
        assert len(agents) == 1

    def test_get_agent_tools(self):
        """Test getting tools for specific agent."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        tools = manager.get_agent_tools("calendar")

        assert tools is not None
        assert "calendar_tools" in tools

    def test_get_agent_tools_invalid(self):
        """Test getting tools for non-existent agent."""
        manager = SubAgentManager()

        tools = manager.get_agent_tools("nonexistent")

        assert tools is None

    def test_get_all_tool_definitions(self):
        """Test getting all tool definitions."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        all_tools = manager.get_all_tool_definitions()

        assert "calendar" in all_tools
        assert len(all_tools["calendar"]) > 0
        assert all_tools["calendar"][0]["type"] == "function"

    def test_manager_repr(self):
        """Test SubAgentManager string representation."""
        manager = SubAgentManager()
        agent = CalendarSubAgent()
        manager.register_agent(agent)

        repr_str = repr(manager)

        assert "SubAgentManager" in repr_str
        assert "calendar" in repr_str
