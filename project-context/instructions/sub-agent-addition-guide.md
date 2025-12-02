# Adding New Sub‑Agent / Skill / MCP Tool

## Overview
This guide describes the **step‑by‑step process** for adding a new sub‑agent, its associated skill prompt, and any required MCP tools to the Family Assistant codebase.  The goal is to keep the changes **isolated, testable, and non‑breaking** so that future coding agents can automate the workflow.

---
### 1. Directory Layout
```
infrastructure/kubernetes/apps/
│   sub‑agents/               # New top‑level folder for all sub‑agents
│   └── <skill_name>/
│       ├── __init__.py       # Makes the folder a Python package
│       ├── agent.py          # Sub‑agent implementation (inherits BaseSubAgent)
│       ├── skill_prompt.md   # Pre‑loaded skill prompt (plain text)
│       └── tools.py          # MCP tool definitions for this skill
```
*All new sub‑agents belong under `apps/sub‑agents/` to keep them separate from core services.*

---
### 2. Create the Skill Prompt
1. Add a markdown file `skill_prompt.md` containing the domain‑specific prompt (5‑10 KB).  
2. Keep the file **pure text** – no code blocks – because it will be loaded as a string at runtime.
3. Example location: `apps/sub‑agents/calendar/skill_prompt.md`.

---
### 3. Implement the Sub‑Agent Class
Create `agent.py` with the following skeleton (copy‑paste and adjust names):
```python
from base_sub_agent import BaseSubAgent
from .tools import CalendarMCPTools

class CalendarSubAgent(BaseSubAgent):
    """Sub‑agent handling calendar‑related requests."""

    def __init__(self):
        # Load the skill prompt once – cached for the lifetime of the process
        with open(__file__.replace('agent.py', 'skill_prompt.md'), 'r') as f:
            skill_prompt = f.read()

        super().__init__(
            agent_id="calendar",
            skill_prompt=skill_prompt,
            tools=[CalendarMCPTools()],
            max_context=3000,  # keep KV‑cache small for local LLMs
        )
```
*Key points:*
- Inherit from `BaseSubAgent` (already defined in the repo).  
- Pass the **skill_prompt** string, not a file path.  
- Register any MCP tools in `tools.py` (see next step).

---
### 4. Define MCP Tools
Create `tools.py` that exposes an MCP‑compatible class:
```python
from mcp import MCPToolBase

class CalendarMCPTools(MCPToolBase):
    """MCP tools for calendar operations."""

    TOOLS = [
        "calendar_create_event",
        "calendar_search_events",
        "calendar_check_conflicts",
        "calendar_get_availability",
    ]

    def __init__(self):
        super().__init__(tool_names=self.TOOLS)

    # Example implementation – replace with real logic later
    async def calendar_create_event(self, **kwargs):
        # Call your internal calendar service or external API
        return {"status": "created", "details": kwargs}
```
*The class must inherit from the project's MCP base class (`MCPToolBase`).  The `TOOLS` list is used by the MCP server to expose the methods.*

---
### 5. Register the Sub‑Agent in `SubAgentManager`
Edit `sub_agent_manager.py` (or the file that builds `SubAgentManager`):
```python
from apps.sub_agents.calendar.agent import CalendarSubAgent

class SubAgentManager:
    def __init__(self):
        self.agents = {
            "calendar": CalendarSubAgent(),
            # add new agents here, e.g. "reminders": RemindersSubAgent(),
        }
        # existing intent classifier stays unchanged
```
*Only add a new key/value pair – no other code changes are required.*

---
### 6. Extend Intent Classification (optional)
If the new skill needs its own intent, update `intent_classifier.py`:
```python
INTENTS["calendar"] = ["schedule", "meeting", "appointment", "calendar"]
```
*If you prefer a rule‑based fallback, you can skip this step and let the router forward unknown intents to a generic "skill‑router".*

---
### 7. Add Unit Tests
Create a test file under `tests/sub_agents/test_calendar.py`:
```python
import pytest
from apps.sub_agents.calendar.agent import CalendarSubAgent

@pytest.mark.asyncio
async def test_calendar_prompt_loaded():
    agent = CalendarSubAgent()
    assert "schedule" in agent.skill_prompt.lower()
```
*Add similar tests for each tool method you implement.*

---
### 8. Update Documentation
1. Add a short entry to `docs/sub-agent‑catalog.md` with:
   - Name
   - Description
   - MCP tool list
2. Commit the changes with a clear message, e.g. `feat(sub‑agents): add calendar sub‑agent`.

---
### 9. Verify Locally
1. Run the FastAPI server (`uvicorn main:app --reload`).  
2. Issue a request that triggers the new intent (e.g. `"Schedule a meeting tomorrow"`).  
3. Confirm the response includes `agent_used: "calendar"` and that the MCP tool is called.

---
## Quick Checklist (copy‑paste for CI)
```
- [ ] Create `apps/sub‑agents/<skill>/` directory
- [ ] Add `skill_prompt.md`
- [ ] Implement `agent.py` (inherits BaseSubAgent)
- [ ] Implement `tools.py` (inherits MCPToolBase)
- [ ] Register in `SubAgentManager`
- [ ] (Optional) Extend `IntentClassifier`
- [ ] Add unit tests under `tests/sub_agents/`
- [ ] Update `docs/sub-agent‑catalog.md`
- [ ] Run local verification
- [ ] Commit with conventional‑commit message
```

---
### Why This Keeps the Code Safe
- **Isolation** – each skill lives in its own package; importing it cannot affect others.  
- **Static registration** – the manager only reads a dictionary; adding a key never overwrites existing entries.  
- **Tests first** – the CI pipeline will catch regressions before they reach production.  
- **MCP abstraction** – tools are exposed through a thin wrapper, so changing the underlying implementation does not ripple through the agent code.

---
**End of Guide**
