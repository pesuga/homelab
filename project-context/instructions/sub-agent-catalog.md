# Sub-Agent Catalog

## Overview

This document catalogs all available sub-agents in the Family Assistant system. Sub-agents are specialized workers that handle specific domain tasks using the Orchestrator-Worker pattern.

**Architecture**: Main Agent (Orchestrator) → Sub-Agent (Worker) → Specialized MCP Tools

## Design Principles

1. **Token Efficiency**: Sub-agents load specialized prompts (5-10K tokens) only when needed
2. **Isolation**: Each sub-agent is self-contained with its own tools and context
3. **Stateless Execution**: Sub-agents don't maintain conversation history (orchestrator does)
4. **MCP Integration**: Tools are exposed via Model Context Protocol for clean abstraction

---

## Available Sub-Agents

### Calendar Sub-Agent

**Agent ID**: `calendar`

**Description**: Specialized agent for handling calendar and scheduling tasks for families.

**Capabilities**:
- Create, update, delete calendar events
- Check for scheduling conflicts
- Find available time slots
- Manage recurring events
- Coordinate family schedules
- Send event reminders

**MCP Tools** (7 total):
1. `calendar_create_event` - Create a new calendar event
   - Parameters: title, start_time, end_time, attendees, location (optional), description (optional), recurring
   - Returns: event_id, status, created_at

2. `calendar_search_events` - Search for events by criteria
   - Parameters: start_date, end_date, attendee (optional), keyword (optional)
   - Returns: events[], total_found

3. `calendar_check_conflicts` - Check if a time slot has conflicts
   - Parameters: start_time, end_time, attendees
   - Returns: has_conflicts, conflicts[], available

4. `calendar_get_availability` - Get free time slots
   - Parameters: start_date, end_date, attendees, min_duration_minutes
   - Returns: free_slots[], attendees

5. `calendar_update_event` - Update an existing event
   - Parameters: event_id, updates
   - Returns: event_id, status, updated_at

6. `calendar_delete_event` - Delete an event
   - Parameters: event_id
   - Returns: event_id, status, deleted_at

7. `calendar_list_upcoming` - List upcoming events
   - Parameters: attendee, days_ahead, limit
   - Returns: events[], attendee, total_events

**Intent Keywords**: schedule, calendar, appointment, meeting, event, when, available, free, busy, book, cancel, reschedule, move, reminder

**Max Context**: 3000 tokens

**Usage Example**:
```python
from sub_agents.manager import get_sub_agent_manager

manager = get_sub_agent_manager()
result = await manager.route_request(
    "Schedule a dentist appointment for Emma tomorrow at 2pm",
    user_context={"user_id": "parent_001"},
    conversation_id="conv_123"
)
```

**Status**: ✅ Implemented (stub tools, ready for real calendar API integration)

---

## Adding New Sub-Agents

To add a new sub-agent, follow the [Sub-Agent Addition Guide](sub-agent-addition-guide.md).

### Quick Checklist

- [ ] Create `sub_agents/<skill>/` directory
- [ ] Add `skill_prompt.md` with specialized prompt (5-10K tokens)
- [ ] Implement `agent.py` (inherits `BaseSubAgent`)
- [ ] Implement `tools.py` (inherits `MCPToolBase`)
- [ ] Register in `manager.py` → `get_sub_agent_manager()`
- [ ] (Optional) Add intent keywords to `IntentClassifier`
- [ ] Add unit tests in `tests/sub_agents/`
- [ ] Update this catalog with new entry
- [ ] Test locally and verify

---

## Planned Sub-Agents

### Homework Sub-Agent (Future)

**Agent ID**: `homework`

**Capabilities**:
- Track homework assignments
- Set study schedules
- Connect with school systems
- Progress tracking
- Deadline management

**Intent Keywords**: homework, assignment, study, test, exam, project, school, class

---

### Health Sub-Agent (Future)

**Agent ID**: `health`

**Capabilities**:
- Track symptoms
- Medication reminders
- Allergy management
- Appointment scheduling with doctors
- Health records access

**Intent Keywords**: symptom, medication, doctor, allergy, health, sick, medicine, prescription

---

### Shopping Sub-Agent (Future)

**Agent ID**: `shopping`

**Capabilities**:
- Manage shopping lists
- Recipe suggestions
- Price comparison
- Order tracking
- Budget management

**Intent Keywords**: buy, grocery, store, shopping, list, recipe, meal, cook

---

## Architecture Documentation

For detailed architecture information, see:
- [Sub-Agent Critique & Proposal](sub-agent-critique-and-proposal.md)
- [Sub-Agent Addition Guide](sub-agent-addition-guide.md)

## Testing

Run sub-agent tests:
```bash
cd services/family-api
pytest tests/sub_agents/ -v
```

Run specific agent tests:
```bash
pytest tests/sub_agents/test_calendar.py -v
```

---

**Last Updated**: 2025-11-26
