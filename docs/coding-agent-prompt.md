# Prompt for a Coding Agent to Implement Sub‑Agent Architecture

## Overview
You are a **coding agent** tasked with turning the design documents into a working implementation inside the **Family Assistant** codebase.  Use the two source documents as the authoritative specifications:

1. **`sub-agent-critique-and-proposal.md`** – contains the architectural critique, the revised orchestrator‑worker proposal, and high‑level component definitions.
2. **`sub-agent-addition-guide.md`** – provides the concrete step‑by‑step guide for adding a new sub‑agent, its skill prompt, and MCP tools.

Your job is to **generate the necessary code, configuration, and documentation** so that a new sub‑agent (e.g., a *calendar* skill) can be added without breaking existing functionality.

---
## Goals
- Implement the **Orchestrator‑Worker** pattern described in the proposal (the main agent retains personality and delegates to sub‑agents via MCP tools).
- Follow the **addition guide** to create a clean, isolated package for the new sub‑agent.
- Ensure the code integrates with the existing FastAPI server, the `SubAgentManager`, and the intent classifier.
- Provide unit tests and update documentation accordingly.

---
## Reference Documents (embed as context)
```
{{FILE:/home/pesu/Rakuflow/systems/homelab/docs/sub-agent-critique-and-proposal.md}}
```
```
{{FILE:/home/pesu/Rakuflow/systems/homelab/docs/sub-agent-addition-guide.md}}
```
*(The coding agent should read the full contents of these files when generating code.)*

---
## Detailed Tasks
1. **Create the sub‑agent package**
   - Directory: `infrastructure/kubernetes/apps/sub‑agents/<skill>/`
   - Files: `__init__.py`, `agent.py`, `skill_prompt.md`, `tools.py`
   - Populate `skill_prompt.md` with a placeholder prompt (e.g., *"You are a calendar assistant…"*).
2. **Implement `agent.py`**
   - Inherit from the project's `BaseSubAgent`.
   - Load the skill prompt at initialization.
   - Register the MCP tool class.
3. **Implement `tools.py`**
   - Subclass the project's `MCPToolBase`.
   - Define the tool list (e.g., `calendar_create_event`, `calendar_search_events`, …).
   - Provide stub async implementations that return a JSON payload.
4. **Register the sub‑agent**
   - Edit `sub_agent_manager.py` (or the appropriate manager) to add the new entry.
   - Ensure the manager imports the new class.
5. **Update Intent Classification (optional)**
   - Add intent keywords for the new skill in `intent_classifier.py`.
6. **Add unit tests** under `tests/sub_agents/` covering:
   - Prompt loading.
   - Each MCP tool stub returns the expected shape.
   - Manager registration.
7. **Update documentation**
   - Add an entry to `docs/sub-agent‑catalog.md` describing the new skill.
   - Add a short section in `README.md` explaining how to invoke the sub‑agent via the main API.
8. **Run local verification**
   - Start the FastAPI server (`uvicorn main:app --reload`).
   - Send a request that triggers the new intent (e.g., *"Schedule a meeting tomorrow"*).
   - Verify the response includes `agent_used: "<skill>"` and that the MCP tool payload is present.
9. **Commit the changes** using a conventional commit message, e.g., `feat(sub‑agents): add <skill> sub‑agent`.

---
## Constraints & Best Practices
- **Isolation** – keep each sub‑agent in its own Python package; never modify global files unless registering the agent.
- **Low token usage** – keep `max_context` ≤ 3000 tokens for local LLMs.
- **MCP abstraction** – tools must be exposed via `MCPToolBase` so the orchestrator can call them without knowing implementation details.
- **Testing first** – all new code must have passing tests before integration.
- **Documentation** – every new file should have a docstring explaining its purpose.

---
## Validation Checklist (copy‑paste into CI)
```
- [ ] Directory `apps/sub‑agents/<skill>/` created
- [ ] `skill_prompt.md` added
- [ ] `agent.py` implements BaseSubAgent correctly
- [ ] `tools.py` defines MCPToolBase subclass with stub methods
- [ ] SubAgentManager registers the new agent
- [ ] (Optional) IntentClassifier updated
- [ ] Unit tests for prompt, tools, and manager exist and pass
- [ ] Documentation `docs/sub-agent‑catalog.md` updated
- [ ] Local verification performed and response contains correct `agent_used`
- [ ] Commit with conventional message
```

---
## Deliverable
Produce a **pull‑request‑ready set of files** matching the tasks above.  The coding agent should output the full diff for each new/modified file, ready to be applied with `git apply`.

---
*End of Prompt*
